from typing import Protocol

from .models.embed import Embed
from .workflows.interactables.components import ComponentBase, LayoutBase

class IMessaging(Protocol):
    async def send_private_message(self, user_id: str, message: str) -> None:
        ...

    async def send_channel_message(
        self,
        server_id: str,
        channel_id: str,
        content: str | Embed,
        components: ComponentBase | list[LayoutBase] | None = None
    ) -> str:
        ...

    async def crosspost_message(
        self,
        server_id: str,
        channel_id: str,
        message_id: str
    ) -> None:
        ...
