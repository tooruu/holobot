from asyncpg.connection import Connection

from holobot.extensions.giveaways.models import ExternalGiveawayItem
from holobot.sdk.database import DatabaseManagerInterface
from holobot.sdk.database.queries import Query
from holobot.sdk.database.queries.enums import Equality
from holobot.sdk.database.statuses import CommandComplete
from holobot.sdk.database.statuses.command_tags import DeleteCommandTag
from holobot.sdk.ioc.decorators import injectable
from holobot.sdk.queries import PaginationResult
from holobot.sdk.utils import UTC, set_time_zone, set_time_zone_nullable
from .iexternal_giveaway_item_repository import IExternalGiveawayItemRepository

_TABLE_NAME = "external_giveaway_items"

@injectable(IExternalGiveawayItemRepository)
class ExternalGiveawayItemRepository(IExternalGiveawayItemRepository):
    def __init__(self, database_manager: DatabaseManagerInterface) -> None:
        self.__database_manager: DatabaseManagerInterface = database_manager

    async def count(self, user_id: str) -> int:
        raise NotImplementedError

    async def get(self, item_id: int) -> ExternalGiveawayItem | None:
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                record = await (Query
                    .select()
                    .columns(
                        "id", "created_at", "start_time", "end_time", "source_name",
                        "item_type", "url", "preview_url", "title"
                    ).from_table(_TABLE_NAME)
                    .where()
                    .field("id", Equality.EQUAL, item_id)
                    .compile()
                    .fetchrow(connection)
                )
                return ExternalGiveawayItemRepository.__parse_record(record) if record else None

    async def get_many(
        self,
        page_index: int,
        page_size: int,
        item_type: str,
        active_only: bool = True
    ) -> PaginationResult[ExternalGiveawayItem]:
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                query = (Query
                    .select()
                    .columns(
                        "id", "created_at", "start_time", "end_time", "source_name",
                        "item_type", "url", "preview_url", "title"
                    )
                    .from_table(_TABLE_NAME)
                    .where()
                    .field("item_type", Equality.EQUAL, item_type)
                )
                if active_only:
                    query = query.and_field(
                        "end_time", Equality.GREATER, "(NOW() AT TIME ZONE 'utc')", True
                    )
                result = await query.paginate("id", page_index, page_size).compile().fetch(connection)
                return PaginationResult(
                    result.page_index,
                    result.page_size,
                    result.total_count,
                    [ExternalGiveawayItemRepository.__parse_record(record) for record in result.records]
                )

    async def exists(self, url: str, active_only: bool = True) -> bool:
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                query = (Query
                    .select()
                    .columns("id")
                    .from_table(_TABLE_NAME)
                    .where()
                    .field("url", Equality.EQUAL, url)
                )
                if active_only:
                    query = query.and_field(
                        "end_time", Equality.GREATER, "(NOW() AT TIME ZONE 'utc')", True
                    )
                return bool(await query.exists().compile().fetchval(connection))

    async def store(self, item: ExternalGiveawayItem) -> None:
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                await Query.insert().in_table(_TABLE_NAME).fields(
                    ("created_at", set_time_zone(item.created_at, None)),
                    ("start_time", set_time_zone_nullable(item.start_time, None)),
                    ("end_time", set_time_zone(item.end_time, None)),
                    ("source_name", item.source_name),
                    ("item_type", item.item_type),
                    ("url", item.url),
                    ("preview_url", item.preview_url),
                    ("title", item.title)
                ).compile().execute(connection)

    async def delete(self, item_id: int) -> None:
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                await Query.delete().from_table(_TABLE_NAME).where().field(
                    "id", Equality.EQUAL, item_id
                ).compile().execute(connection)

    async def delete_expired(self) -> int:
        async with self.__database_manager.acquire_connection() as connection:
            connection: Connection
            async with connection.transaction():
                status: CommandComplete[DeleteCommandTag] = await (Query
                    .delete()
                    .from_table(_TABLE_NAME)
                    .where()
                    .field("end_time", Equality.LESS, "(NOW() at time zone 'utc') - interval '7 days'", True)
                    .compile()
                    .execute(connection)
                )
                return status.command_tag.rows

    @staticmethod
    def __parse_record(record) -> ExternalGiveawayItem:
        return ExternalGiveawayItem(
            record["id"],
            set_time_zone(record["created_at"], UTC),
            set_time_zone(record["start_time"], UTC),
            set_time_zone(record["end_time"], UTC),
            record["source_name"],
            record["item_type"],
            record["url"],
            record["preview_url"],
            record["title"]
        )
