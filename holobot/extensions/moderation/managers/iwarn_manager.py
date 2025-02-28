from datetime import timedelta
from typing import Protocol

from holobot.sdk.queries import PaginationResult
from ..models import WarnStrike

class IWarnManager(Protocol):
    async def get_warns(
        self,
        server_id: str,
        user_id: str,
        page_index: int,
        page_size: int
    ) -> PaginationResult[WarnStrike]:
        ...

    async def warn_user(
        self,
        server_id: str,
        user_id: str,
        reason: str,
        warner_id: str
    ) -> WarnStrike:
        ...

    async def clear_warns_for_user(self, server_id: str, user_id: str) -> int:
        ...

    async def clear_warns_for_server(self, server_id: str) -> int:
        ...

    async def enable_auto_mute(
        self,
        server_id: str,
        warn_count: int,
        duration: timedelta | None
    ) -> None:
        ...

    async def disable_auto_mute(self, server_id: str) -> None:
        ...

    async def enable_auto_kick(self, server_id: str, warn_count: int) -> None:
        ...

    async def disable_auto_kick(self, server_id: str) -> None:
        ...

    async def enable_auto_ban(self, server_id: str, warn_count: int) -> None:
        ...

    async def disable_auto_ban(self, server_id: str) -> None:
        ...

    async def get_warn_decay(self, server_id: str) -> timedelta | None:
        ...

    async def set_warn_decay(
        self,
        server_id: str,
        decay_time: timedelta | None
    ) -> None:
        ...
