from .moderation_command_base import ModerationCommandBase
from ..enums import ModeratorPermission
from ..managers import IPermissionManager
from discord_slash.context import SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_choice, create_option
from holobot.discord.sdk.commands import CommandInterface
from holobot.discord.sdk.enums import Permission
from holobot.discord.sdk.utils import get_user_id, reply
from holobot.sdk.ioc.decorators import injectable

@injectable(CommandInterface)
class AddModeratorPermissionCommand(ModerationCommandBase):
    def __init__(self, permission_manager: IPermissionManager) -> None:
        super().__init__("add")
        self.group_name = "moderation"
        self.subgroup_name = "permissions"
        self.description = "Assign a moderator permission to a user."
        self.options = [
            create_option("user", "The mention of the user to modify.", SlashCommandOptionType.STRING, True),
            create_option("permission", "The permission to assign.", SlashCommandOptionType.INTEGER, True, [
                create_choice(ModeratorPermission.MUTE, "Mute users"),
                create_choice(ModeratorPermission.KICK, "Kick users"),
                create_choice(ModeratorPermission.BAN, "Ban users"),
                create_choice(ModeratorPermission.VIEW_LOGS, "View logs")
            ])
        ]
        self.required_permissions = Permission.ADMINISTRATOR
        self.__permission_manager: IPermissionManager = permission_manager
    
    async def execute(self, context: SlashContext, user: str, permission: int) -> None:
        if (user_id := get_user_id(user)) is None:
            await reply(context, "You must mention a user correctly.")
            return
        typed_permission = ModeratorPermission(permission)
        await self.__permission_manager.add_permissions(str(context.guild_id), user_id, typed_permission)
        await reply(context, f"{user} has been assigned the permission '{typed_permission.textify()}''.")
