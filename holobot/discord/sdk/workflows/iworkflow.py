from abc import ABCMeta, abstractmethod
from typing import Tuple

from .interactables import Interactable
from ..enums import Permission

class IWorkflow(metaclass=ABCMeta):
    @property
    @abstractmethod
    def name(self) -> str:
        """Gets the name of the workflow which is also its unique identifier.

        :return: The name of the workflow.
        :rtype: str
        """

    @property
    @abstractmethod
    def required_permissions(self) -> Permission:
        """Gets an enumeration of the permissions required to invoke interactables of the workflow.

        These permissions will be required by all interactables of the workflow,
        combined with the optionally specified additional permissions
        of a specific workflow step.

        :return: The permissions required by the workflow's interactables.
        :rtype: Permission
        """

    @property
    @abstractmethod
    def interactables(self) -> Tuple[Interactable, ...]:
        """Gets the list of interactable registrations associated to the workflow.

        :return: The associated interactable registrations.
        :rtype: Tuple[InteractableRegistration, ...]
        """
