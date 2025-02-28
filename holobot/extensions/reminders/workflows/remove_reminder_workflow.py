from holobot.discord.sdk.actions import ReplyAction
from holobot.discord.sdk.workflows import IWorkflow, WorkflowBase
from holobot.discord.sdk.workflows.interactables.decorators import command
from holobot.discord.sdk.workflows.interactables.enums import OptionType
from holobot.discord.sdk.workflows.interactables.models import InteractionResponse, Option
from holobot.discord.sdk.workflows.models import ServerChatInteractionContext
from holobot.sdk.i18n import II18nProvider
from holobot.sdk.ioc.decorators import injectable
from holobot.sdk.logging import ILoggerFactory
from .. import ReminderManagerInterface
from ..exceptions import InvalidReminderError

@injectable(IWorkflow)
class RemoveReminderWorkflow(WorkflowBase):
    def __init__(
        self,
        i18n_provider: II18nProvider,
        logger_factory: ILoggerFactory,
        reminder_manager: ReminderManagerInterface
    ) -> None:
        super().__init__()
        self.__i18n_provider = i18n_provider
        self.__logger = logger_factory.create(RemoveReminderWorkflow)
        self.__reminder_manager = reminder_manager

    @command(
        description="Removes a reminder.",
        name="remove",
        group_name="reminder",
        options=(
            Option("id", "The identifier of the reminder.", OptionType.INTEGER),
        )
    )
    async def remove_reminder(
        self,
        context: ServerChatInteractionContext,
        id: int
    ) -> InteractionResponse:
        try:
            await self.__reminder_manager.delete_reminder(context.author_id, id)
            self.__logger.debug("Deleted a reminder", user_id=context.author_id, reminder_id=id)
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.reminders.remove_reminder_workflow.reminder_deleted"
                    )
                )
            )
        except InvalidReminderError:
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.reminders.remove_reminder_workflow.reminder_not_found_error"
                    )
                )
            )
