from holobot.discord.sdk.actions import ReplyAction
from holobot.discord.sdk.workflows import IWorkflow, WorkflowBase
from holobot.discord.sdk.workflows.interactables.decorators import command
from holobot.discord.sdk.workflows.interactables.enums import OptionType
from holobot.discord.sdk.workflows.interactables.models import InteractionResponse, Option
from holobot.discord.sdk.workflows.models import ServerChatInteractionContext
from holobot.sdk.i18n import II18nProvider
from holobot.sdk.ioc.decorators import injectable
from .. import TodoItemManagerInterface
from ..exceptions import InvalidTodoItemError

@injectable(IWorkflow)
class RemoveTodoItemWorkflow(WorkflowBase):
    def __init__(
        self,
        i18n_provider: II18nProvider,
        todo_item_manager: TodoItemManagerInterface
    ) -> None:
        super().__init__()
        self.__i18n_provider = i18n_provider
        self.__todo_item_manager = todo_item_manager
    
    @command(
        description="Removes a to-do item from your list.",
        name="remove",
        group_name="todo",
        options=(
            Option("identifier", "The identifier of the to-do item.", OptionType.INTEGER),
        )
    )
    async def remove_todo_item(
        self,
        context: ServerChatInteractionContext,
        identifier: int
    ) -> InteractionResponse:
        try:
            await self.__todo_item_manager.delete_by_user(context.author_id, identifier)
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.todo_lists.remove_todo_item_workflow.item_deleted"
                    )
                )
            )
        except InvalidTodoItemError:
            return InteractionResponse(
                action=ReplyAction(
                    content=self.__i18n_provider.get(
                        "extensions.todo_lists.remove_todo_item_workflow.no_todo_item_error"
                    )
                )
            )
