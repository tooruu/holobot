import hikari
from hikari import CommandInteraction, ComponentInteraction

from holobot.discord.bot import Bot
from holobot.discord.workflows import IInteractionProcessor
from holobot.discord.workflows.processors import IMenuItemProcessor
from holobot.sdk.ioc.decorators import injectable
from .discord_event_listener_base import DiscordEventListenerBase
from .igeneric_discord_event_listener import IGenericDiscordEventListener

_EVENT_TYPE = hikari.InteractionCreateEvent

@injectable(IGenericDiscordEventListener)
class InteractionCreatedEventListener(DiscordEventListenerBase[_EVENT_TYPE]):
    def __init__(
        self,
        command_processor: IInteractionProcessor[CommandInteraction],
        component_processor: IInteractionProcessor[ComponentInteraction],
        menu_item_processor: IMenuItemProcessor
    ) -> None:
        super().__init__()
        self.__command_processor = command_processor
        self.__component_processor = component_processor
        self.__menu_item_processor = menu_item_processor

    @property
    def event_type(self) -> type:
        return _EVENT_TYPE

    async def on_event(self, bot: Bot, event: _EVENT_TYPE) -> None:
        match event.interaction:
            case hikari.CommandInteraction(command_type=hikari.CommandType.SLASH):
                await self.__command_processor.process(event.interaction)
            case hikari.CommandInteraction(command_type=hikari.CommandType.USER | hikari.CommandType.MESSAGE):
                await self.__menu_item_processor.process(event.interaction)
            case hikari.ComponentInteraction():
                await self.__component_processor.process(event.interaction)
