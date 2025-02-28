from collections.abc import Sequence
from typing import Any, Protocol

from holobot.sdk.diagnostics import ExecutionContextData

class ILogger(Protocol):
    """Interface for a service used for writing logs.

    Where the logs appear depend on the implementation
    of the interface (such as the console or a file).
    """

    def trace(self, message: str, **kwargs: Any) -> None:
        ...

    def debug(self, message: str, **kwargs: Any) -> None:
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        ...

    def error(
        self,
        message: str,
        exception: Exception | None = None,
        **kwargs: Any
    ) -> None:
        ...

    def critical(self, message: str, **kwargs: Any) -> None:
        ...

    def exception(self, message: str, **kwargs: Any) -> None:
        ...

    def diagnostics(self, message:str, events: Sequence[ExecutionContextData]) -> None:
        """Logs the diagnostics information of the specified events.

        :param message: The message to be logged.
        :type message: str
        :param events: A sequence of execution context data associated to each event.
        :type events: Sequence[ExecutionContextData]
        """
        ...
