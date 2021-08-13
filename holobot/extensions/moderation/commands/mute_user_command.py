from .moderation_command_base import ModerationCommandBase
from .. import IConfigProvider
from ..constants import MUTED_ROLE_NAME
from ..enums import ModeratorPermission
from discord.abc import GuildChannel
from discord.errors import Forbidden
from discord.guild import Guild
from discord.member import Member
from discord.role import Role
from discord.utils import get
from discord_slash.context import SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
from holobot.discord.sdk.commands import CommandInterface
from holobot.discord.sdk.utils import get_user_id, reply
from holobot.sdk.integration import MessagingInterface
from holobot.sdk.ioc.decorators import injectable
from typing import List, Optional

@injectable(CommandInterface)
class MuteUserCommand(ModerationCommandBase):
    def __init__(self, config_provider: IConfigProvider, messaging: MessagingInterface) -> None:
        super().__init__("mute")
        self.group_name = "moderation"
        self.description = "Mutes a user."
        self.options = [
            create_option("user", "The mention of the user to mute.", SlashCommandOptionType.STRING, True),
            create_option("reason", "The reason of the punishment.", SlashCommandOptionType.STRING, True),
            create_option("duration", "The duration after which to lift the mute. Eg. 1h or 30m.", SlashCommandOptionType.STRING, False)
        ]
        self.required_moderator_permissions = ModeratorPermission.MUTE_USERS
        self.__config_provider: IConfigProvider = config_provider
        self.__messaging: MessagingInterface = messaging
    
    async def execute(self, context: SlashContext, user: str, reason: str, duration: Optional[str] = None) -> None:
        # TODO Auto unmute after the duration.
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
            muted_role = await self.__get_or_create_muted_role(context.guild, context.guild.roles)
        except Forbidden:
            await reply(context, "I cannot assign/create a 'Muted' role. Have you given me role management permissions?")
            return

        try:
            await member.add_roles(muted_role)
        except Forbidden:
            await reply(context, (
                "I cannot add the 'Muted' role.\n"
                "Have you given me user management permissions?\n"
                "Do they have a higher ranking role?"
            ))
            return

        await reply(context, f"{member.mention} has been muted. Reason: {reason}")
        await self.__messaging.send_dm(user_id, f"You have been muted in {context.guild.name} by {context.author.name} with the reason '{reason}'. I'm sorry this happened to you.")
    
    async def __get_or_create_muted_role(self, guild: Guild, roles: List[Role]) -> Role:
        role = get(roles, name=MUTED_ROLE_NAME)
        if role is not None:
            return role

        role = await guild.create_role(name=MUTED_ROLE_NAME, reason="Used for muting people in text channels.")
        for channel in guild.channels:
            channel: GuildChannel
            await channel.set_permissions(role, send_messages=False)
        return role
