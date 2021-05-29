from typing import List, Type, TypeVar

TService = TypeVar("TService")

class ServiceCollectionInterface:
    async def close(self):
        pass

    def get(self, type: Type[TService]) -> TService:
        raise NotImplementedError
    
    def get_all(self, type: Type[TService]) -> List[TService]:
        raise NotImplementedError
