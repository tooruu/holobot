from .exceptions import InvalidTodoItemError, TooManyTodoItemsError
from .models import TodoItem
from .repositories import TodoItemRepositoryInterface
from .todo_item_manager_interface import TodoItemManagerInterface
from holobot.sdk.configs import ConfiguratorInterface
from holobot.sdk.exceptions import ArgumentOutOfRangeError
from holobot.sdk.ioc.decorators import injectable
from holobot.sdk.logging import ILoggerFactory
from holobot.sdk.queries import PaginationResult

@injectable(TodoItemManagerInterface)
class TodoItemManager(TodoItemManagerInterface):
    def __init__(
        self,
        configurator: ConfiguratorInterface,
        logger_factory: ILoggerFactory,
        todo_item_repository: TodoItemRepositoryInterface
    ) -> None:
        super().__init__()
        self.__configurator = configurator
        self.__logger = logger_factory.create(TodoItemManager)
        self.__todo_item_repository: TodoItemRepositoryInterface = todo_item_repository
        self.__todo_items_per_user_max: int = self.__configurator.get("TodoLists", "TodoItemsPerUserMax", 5)
        self.__message_length_min: int = self.__configurator.get("TodoLists", "MessageLengthMin", 10)
        self.__message_length_max: int = self.__configurator.get("TodoLists", "MessageLengthMax", 192)
        
    async def get_by_user(self, user_id: str, page_index: int, page_size: int) -> PaginationResult[TodoItem]:
        return await self.__todo_item_repository.get_many(user_id, page_index, page_size)

    async def add_todo_item(self, todo_item: TodoItem) -> None:
        if not (self.__message_length_min <= len(todo_item.message) <= self.__message_length_max):
            raise ArgumentOutOfRangeError("message", str(self.__message_length_min), str(self.__message_length_max))

        await self.__assert_todo_item_count(todo_item.user_id)
        await self.__todo_item_repository.store(todo_item)
        self.__logger.debug("Set new to-do item", user_id=todo_item.user_id)
    
    async def delete_by_user(self, user_id: str, todo_item_id: int) -> None:
        if not user_id:
            raise ValueError("The user identifier cannot be none.")
        
        deleted_count = await self.__todo_item_repository.delete_by_user(user_id, todo_item_id)
        if deleted_count == 0:
            raise InvalidTodoItemError("The specified to-do item doesn't exist or belong to the specified user.")
            
    async def delete_all(self, user_id: str) -> int:
        if not user_id:
            raise ValueError("The user identifier cannot be none.")
        
        return await self.__todo_item_repository.delete_all(user_id)

    async def __assert_todo_item_count(self, user_id: str) -> None:
        count = await self.__todo_item_repository.count(user_id)
        if count >= self.__todo_items_per_user_max:
            raise TooManyTodoItemsError(count)
