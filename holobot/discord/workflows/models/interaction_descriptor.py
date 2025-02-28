from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from holobot.discord.sdk.workflows import IWorkflow
from holobot.discord.sdk.workflows.interactables import Interactable

TInteractable = TypeVar("TInteractable", bound=Interactable)

@dataclass(kw_only=True)
class InteractionDescriptor(Generic[TInteractable]):
    workflow: IWorkflow | None
    interactable: TInteractable | None
    arguments: dict[str, Any] = field(default_factory=dict)

    initiator_id: str
    """The identifier of the user who initiated this interaction."""

    bound_user_id: str
    """The identifier of the user who initiated the workflow."""
