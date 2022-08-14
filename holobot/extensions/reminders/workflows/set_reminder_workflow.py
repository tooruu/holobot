from typing import Optional

from .. import ReminderManagerInterface
from ..exceptions import InvalidReminderConfigError, TooManyRemindersError
from ..models import ReminderConfig
from holobot.discord.sdk.actions import ReplyAction
from holobot.discord.sdk.workflows import IWorkflow, WorkflowBase
from holobot.discord.sdk.workflows.interactables.decorators import command
from holobot.discord.sdk.workflows.interactables.models import InteractionResponse, Option
from holobot.discord.sdk.workflows.models import ServerChatInteractionContext
from holobot.sdk.chrono import parse_interval
from holobot.sdk.exceptions import ArgumentError, ArgumentOutOfRangeError
from holobot.sdk.i18n import II18nProvider
from holobot.sdk.ioc.decorators import injectable
from holobot.sdk.logging import ILoggerFactory

@injectable(IWorkflow)
class SetReminderWorkflow(WorkflowBase):
    def __init__(
        self,
        i18n_provider: II18nProvider,
        logger_factory: ILoggerFactory,
        reminder_manager: ReminderManagerInterface
    ) -> None:
        super().__init__()
        self.__i18n_provider = i18n_provider
        self.__logger = logger_factory.create(SetReminderWorkflow)
        self.__reminder_manager = reminder_manager

    @command(
        description="Sets a new reminder.",
        name="set",
        group_name="reminder",
        options=(
            Option("message", "The message you'd like sent to you."),
            Option("in_time", "After the specified time passes. Eg. 1h30m or 01:30.", is_mandatory=False),
            Option("at_time", "At a specific moment in time. Eg. 15:30 or 15h30m.", is_mandatory=False),
            Option("every_interval", "Repeat in intervals. Eg. 1h30m, 01:30 or day/week.", is_mandatory=False)
        )
    )
    async def set_reminder(
        self,
        context: ServerChatInteractionContext,
        message: str,
        in_time: Optional[str] = None,
        at_time: Optional[str] = None,
        every_interval: Optional[str] = None
    ) -> InteractionResponse:
        reminder_config = ReminderConfig()
        if in_time is not None and len(in_time) > 0:
            reminder_config.in_time = parse_interval(in_time)
        if at_time is not None and len(at_time) > 0:
            reminder_config.at_time = parse_interval(at_time)
        if every_interval is not None and len(every_interval) > 0:
            reminder_config.every_interval = parse_interval(every_interval)
        reminder_config.message = message

        try:
            reminder = await self.__reminder_manager.set_reminder(context.author_id, reminder_config)
            self.__logger.debug("Set new reminder", user_id=context.author_id, reminder_id=reminder.id)
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.reminders.set_reminder_workflow.reminder_set",
                        { "time": reminder.next_trigger }
                    )
                )
            )
        except ArgumentOutOfRangeError as error:
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.reminders.set_reminder_workflow.message_out_of_range_error",
                        { "min": error.lower_bound, "max": error.upper_bound }
                    )
                )
            )
        except ArgumentError as error:
            if error.argument_name == "occurrence":
                return InteractionResponse(
                    action=ReplyAction(
                        content=self.__i18n_provider.get(
                            "extensions.reminders.set_reminder_workflow.missing_time_error"
                        )
                    )
                )
            else: raise
        except InvalidReminderConfigError as error:
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.reminders.set_reminder_workflow.invalid_params_error",
                        { "param1": error.param1, "param2": error.param2 }
                    )
                )
            )
        except TooManyRemindersError:
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.reminders.set_reminder_workflow.too_many_reminders_error"
                    )
                )
            )
