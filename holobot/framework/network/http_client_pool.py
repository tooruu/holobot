from collections.abc import Callable, Generator
from types import coroutine
from typing import Any

from aiohttp import ClientSession, TCPConnector
from aiohttp.client import ClientTimeout
from aiohttp.web_exceptions import HTTPError, HTTPForbidden, HTTPNotFound
from multidict import CIMultiDict

from holobot.framework.configs import EnvironmentOptions
from holobot.sdk.configs import IOptions
from holobot.sdk.ioc.decorators import injectable
from holobot.sdk.lifecycle import IStartable
from holobot.sdk.logging import ILoggerFactory
from holobot.sdk.network import HttpClientPoolInterface
from holobot.sdk.network.exceptions import HttpStatusError, ImATeapotError, TooManyRequestsError

DEFAULT_TIMEOUT = ClientTimeout(total=5)

# https://julien.danjou.info/python-and-fast-http-clients/
@injectable(IStartable)
@injectable(HttpClientPoolInterface)
class HttpClientPool(HttpClientPoolInterface, IStartable):
    def __init__(
        self,
        logger_factory: ILoggerFactory,
        options: IOptions[EnvironmentOptions]
    ) -> None:
        self.__error_map: dict[int, Callable[[CIMultiDict], Exception]] = {
            403: lambda _: HTTPForbidden(),
            404: lambda _: HTTPNotFound(),
            ImATeapotError.STATUS_CODE: ImATeapotError.from_headers,
            TooManyRequestsError.STATUS_CODE: TooManyRequestsError.from_headers
        }
        self.__session = ClientSession(
            connector=TCPConnector(limit=options.value.HttpPoolSize)
        )
        self.__logger = logger_factory.create(HttpClientPool)

    @coroutine
    def start(self) -> Generator[None, None, None]:
        yield

    async def stop(self):
        self.__logger.debug("Closing session...")
        await self.__session.close()
        self.__logger.debug("Successfully closed session")

    async def get(self, url: str, query_parameters: dict[str, Any] | None = None) -> Any:
        try:
            async with self.__session.get(url, params=query_parameters, timeout=DEFAULT_TIMEOUT) as response:
                return await response.json()
        except HTTPError as error:
            self.__raise_on_error(error)

    async def post(self, url: str, json: dict[str, Any]) -> Any:
        try:
            async with self.__session.post(url, json=json, timeout=DEFAULT_TIMEOUT) as response:
                return await response.json()
        except HTTPError as error:
            self.__raise_on_error(error)

    def __raise_on_error(self, error: HTTPError):
        if (error_factory := self.__error_map.get(error.status)):
            raise error_factory(error.headers)
        raise HttpStatusError(error.status)
