from holobot.discord.sdk.actions import ReplyAction
from holobot.discord.sdk.enums import Permission
from holobot.discord.sdk.workflows import IWorkflow, WorkflowBase
from holobot.discord.sdk.workflows.interactables.models import InteractionResponse
from holobot.discord.sdk.workflows.models import ServerChatInteractionContext
from holobot.sdk.i18n import II18nProvider
from holobot.sdk.ioc.decorators import injectable
from ..managers import IWarnManager
from .interactables.decorators import moderation_command
from .responses import AutoBanToggledResponse

@injectable(IWorkflow)
class DisableAutoBanWorkflow(WorkflowBase):
    def __init__(
        self,
        i18n_provider: II18nProvider,
        warn_manager: IWarnManager
    ) -> None:
        super().__init__()
        self.__i18n_provider = i18n_provider
        self.__warn_manager = warn_manager

    @moderation_command(
        description="Disables automatic user banishment.",
        name="disableban",
        group_name="moderation",
        subgroup_name="auto",
        required_permissions=Permission.ADMINISTRATOR
    )
    async def disable_auto_ban(
        self,
        context: ServerChatInteractionContext
    ) -> InteractionResponse:
        await self.__warn_manager.disable_auto_ban(context.server_id)
        return AutoBanToggledResponse(
            author_id=context.author_id,
            action=ReplyAction(
                content=self.__i18n_provider.get(
                    "extensions.moderation.disable_auto_ban_workflow.auto_ban_disabled"
                )
            )
        )
