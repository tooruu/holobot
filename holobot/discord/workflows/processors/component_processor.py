from typing import Tuple
from uuid import uuid4

from hikari import ComponentInteraction

from holobot.discord.actions import IActionProcessor
from holobot.discord.sdk.models import InteractionContext
from holobot.discord.sdk.workflows.interactables import Component
from holobot.discord.sdk.workflows.models import ServerChatInteractionContext
from holobot.discord.sdk.workflows.rules import IWorkflowExecutionRule
from holobot.discord.workflows import IInteractionProcessor, InteractionProcessorBase, IWorkflowRegistry
from holobot.discord.workflows.models import InteractionDescriptor
from holobot.discord.workflows.transformers import IComponentTransformer
from holobot.sdk.ioc.decorators import injectable
from holobot.sdk.logging import LogInterface

@injectable(IInteractionProcessor[ComponentInteraction])
class ComponentProcessor(InteractionProcessorBase[ComponentInteraction, Component]):
    def __init__(
        self,
        action_processor: IActionProcessor,
        component_transformer: IComponentTransformer,
        log: LogInterface,
        workflow_execution_rules: Tuple[IWorkflowExecutionRule, ...],
        workflow_registry: IWorkflowRegistry
    ) -> None:
        super().__init__(action_processor, log, workflow_execution_rules)
        self.__component_transformer = component_transformer
        self.__workflow_registry = workflow_registry

    def _get_interactable_descriptor(
        self,
        interaction: ComponentInteraction
    ) -> InteractionDescriptor[Component]:
        component_id = interaction.custom_id.split("~", 1)[0]
        invocation_target = self.__workflow_registry.get_component(component_id)
        state = self.__component_transformer.transform_state(
            invocation_target[1].component_type,
            interaction
        ) if invocation_target else None
        return InteractionDescriptor(
            workflow=invocation_target[0] if invocation_target else None,
            interactable=invocation_target[1] if invocation_target else None,
            arguments={
                "state": state
            }
        )

    async def _get_interaction_context(
        self,
        interaction: ComponentInteraction
    ) -> InteractionContext:
        # TODO Support non-server specific commands.
        if not interaction.guild_id:
            raise NotImplementedError("Non-server specific commands are not supported.")

        return ServerChatInteractionContext(
            request_id=uuid4(),
            author_id=str(interaction.user.id),
            author_name=interaction.user.username,
            author_nickname=interaction.member.nickname if interaction.member else None,
            server_id=str(interaction.guild_id),
            server_name=await ComponentProcessor.__get_server_name(interaction),
            channel_id=str(interaction.channel_id)
        )

    @staticmethod
    async def __get_server_name(interaction: ComponentInteraction) -> str:
        server = interaction.get_guild()
        if server:
            return server.name

        server = await interaction.fetch_guild()
        return server.name if server else "Unknown Server"
