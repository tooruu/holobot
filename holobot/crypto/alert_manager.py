from asyncpg.connection import Connection
from decimal import Decimal
from holobot.crypto.alert_manager_interface import AlertManagerInterface
from holobot.crypto.enums.price_direction import PriceDirection
from holobot.crypto.models.alert import Alert
from holobot.crypto.models.symbol_update_event import SymbolUpdateEvent
from holobot.database.database_manager_interface import DatabaseManagerInterface
from holobot.dependency_injection.service_collection_interface import ServiceCollectionInterface
from holobot.display.display_interface import DisplayInterface
from holobot.reactive.listener_interface import ListenerInterface
from typing import List

class AlertManager(AlertManagerInterface, ListenerInterface[SymbolUpdateEvent]):
    def __init__(self, service_collection: ServiceCollectionInterface):
        self.__database_manager = service_collection.get(DatabaseManagerInterface)
        self.__display = service_collection.get(DisplayInterface)
    
    async def add(self, user_id: str, symbol: str, direction: PriceDirection, value: Decimal):
        print(f"[AlertManager] Adding alert... {{ UserId = {user_id}, Symbol = {symbol} }}")
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                row_count = await connection.fetchval(
                    "SELECT COUNT(*) FROM crypto_alerts WHERE user_id = $1 AND symbol = $2 AND direction = $3",
                    user_id, symbol, direction
                )
                if row_count != 0:
                    await connection.execute(
                        "UPDATE crypto_alerts SET price = $1 WHERE user_id = $2 AND symbol = $3 AND direction = $4",
                        value, user_id, symbol, direction
                    )
                    return
                # TODO Limit the maximum number of alerts per user.
                await connection.execute(
                    "INSERT INTO crypto_alerts (user_id, symbol, direction, price) VALUES ($1, $2, $3, $4)",
                    user_id, symbol, direction, value
                )
        print(f"[AlertManager] Added alert. {{ UserId = {user_id}, Symbol = {symbol} }}")

    async def get_many(self, user_id: str, start_offset: int, page_size: int) -> List[Alert]:
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                records = await connection.fetch("SELECT symbol, direction, price FROM crypto_alerts WHERE user_id = $1 LIMIT $3 OFFSET $2", str(user_id), start_offset, page_size)
                return [Alert(
                    record["symbol"],
                    PriceDirection(record["direction"]),
                    Decimal(record["price"])
                ) for record in records]

    async def remove_many(self, user_id: str, symbol: str) -> List[Alert]:
        print(f"[AlertManager] Deleting alerts... {{ UserId = {user_id}, Symbol = {symbol} }}")
        deleted_alerts = []
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                records = await connection.fetch("DELETE FROM crypto_alerts WHERE user_id = $1 AND symbol = $2 RETURNING direction, price", user_id, symbol)
                for record in records:
                    deleted_alerts.append(Alert(symbol, PriceDirection(record["direction"]), Decimal(record["price"])))
        print(f"[AlertManager] Deleted alerts. {{ UserId = {user_id}, Symbol = {symbol} }}")
        return deleted_alerts

    async def on_event(self, event: SymbolUpdateEvent):
        sent_notifications = set()
        record_ids = set()
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                async for record in connection.cursor("SELECT id, user_id, direction, price FROM crypto_alerts WHERE symbol = $1 AND notified_at::date != current_date", event.symbol):
                    user_id: str = record["user_id"]
                    direction: PriceDirection = PriceDirection(record["direction"])
                    notification_id = f"{user_id}/{direction.value}"
                    if notification_id in sent_notifications:
                        continue
                    target_price: Decimal = Decimal(record["price"])
                    if not self.__should_notify(event, direction, target_price):
                        continue
                    sent_notifications.add(notification_id)
                    record_ids.add(str(record["id"]))
                    await self.__try_notify(int(user_id), event)
                if len(record_ids) == 0:
                    return
                await connection.execute("UPDATE crypto_alerts SET notified_at = NOW() WHERE id IN ({})".format(
                    ",".join(record_ids)
                ))
                print(f"[AlertManager] Notified users. {{ AlertCount = {len(record_ids)}, Symbol = {event.symbol} }}")
    
    def __should_notify(self, event: SymbolUpdateEvent, direction: PriceDirection, target_price: Decimal):
        if direction == PriceDirection.ABOVE and event.price >= target_price:
            return True
        if direction == PriceDirection.BELOW and event.price <= target_price:
            return True
        return False
    
    async def __try_notify(self, user_id: int, event: SymbolUpdateEvent):
        try:
            await self.__display.send_dm(user_id, f"{event.symbol} price is {event.price:,.8f}.")
        except Exception as error:
            print(f"[AlertManager] Failed to notify the user '{user_id}': {error}")