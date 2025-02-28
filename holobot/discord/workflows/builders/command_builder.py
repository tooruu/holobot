from __future__ import annotations

from collections.abc import Callable

from hikari.api.special_endpoints import SlashCommandBuilder

from holobot.discord.sdk.workflows.interactables.models import Option
from .utils import transform_option

class CommandBuilder:
    def __init__(
        self,
        name: str,
        description: str,
        slash_command_builder_factory: Callable[[str, str], SlashCommandBuilder]
    ) -> None:
        self.__name: str = name
        self.__description: str = description
        self.__slash_command_builder_factory: Callable[[str, str], SlashCommandBuilder] = slash_command_builder_factory
        self.__options: list[Option] = []

    def with_option(self, option: Option) -> CommandBuilder:
        self.__options.append(option)
        return self

    def build(self) -> SlashCommandBuilder:
        builder = self.__slash_command_builder_factory(self.__name, self.__description)
        for option in self.__options:
            builder.add_option(transform_option(option))
        return builder
