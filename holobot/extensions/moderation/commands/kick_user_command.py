from .moderation_command_base import ModerationCommandBase
from .. import IConfigProvider
from ..enums import ModeratorPermission
from discord.errors import Forbidden
from discord.member import Member
from discord_slash.context import SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
from holobot.discord.sdk.commands import CommandInterface
from holobot.discord.sdk.utils import get_user_id, reply
from holobot.sdk.ioc.decorators import injectable

@injectable(CommandInterface)
class KickUserCommand(ModerationCommandBase):
    def __init__(self, config_provider: IConfigProvider) -> None:
        super().__init__("kick")
        self.group_name = "moderation"
        self.description = "Kicks a user from the server. The user can rejoin with an invitation."
        self.options = [
            create_option("user", "The mention of the user to kick.", SlashCommandOptionType.STRING, True),
            create_option("reason", "The reason of the punishment.", SlashCommandOptionType.STRING, True)
        ]
        self.required_moderator_permissions = ModeratorPermission.MUTE_USERS
        self.__config_provider: IConfigProvider = config_provider
    
    async def execute(self, context: SlashContext, user: str, reason: str) -> None:
        reason = reason.strip()
        if (user_id := get_user_id(user)) is None:
            await reply(context, "You must mention a user correctly.")
            return
        if context.guild is None:
            await reply(context, "You may use this command in a server only.")
            return
        reason_length_range = self.__config_provider.get_reason_length_range()
        if not len(reason) in reason_length_range:
            await reply(context, f"The reason parameter's length must be between {reason_length_range.lower_bound} and {reason_length_range.upper_bound}.")
            return

        member = context.guild.get_member(int(user_id))
        if member is None:
            await reply(context, "The user you mentioned cannot be found.")
            return
        if not isinstance(member, Member):
            await reply(context, "I'm sorry, but something went wrong internally. Please, try again later or contact your server administrator.")
            return
        
        try:
            await member.kick(reason=reason)
        except Forbidden:
            await reply(context, (
                "I cannot kick the user.\n"
                "Have you given me user management permissions?\n"
                "Do they have a higher ranking role?"
            ))
            return

        await reply(context, f"{member.mention} has been kicked. Reason: {reason}")
