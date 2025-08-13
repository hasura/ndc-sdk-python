from typing import Generic, TypeVar, Any
from typing import Optional
from abc import ABC, abstractmethod
from ndc_sdk_python.models import (
    Capabilities,
    SchemaResponse,
    QueryRequest,
    QueryResponse,
    ExplainResponse,
    MutationRequest,
    MutationResponse
)
from pydantic import BaseModel

ConfigurationType = TypeVar('ConfigurationType', bound=BaseModel)
StateType = TypeVar('StateType', bound=BaseModel)


class Connector(ABC, Generic[ConfigurationType, StateType]):

    def __init__(self, configuration_type, state_type):
        self.configuration_type = configuration_type
        self.state_type = state_type

    @abstractmethod
    async def parse_configuration(self, configuration_dir: str) -> ConfigurationType:
        pass

    @abstractmethod
    async def try_init_state(self, configuration: ConfigurationType, metrics: Any) -> StateType:
        pass

    @abstractmethod
    async def fetch_metrics(self, configuration: ConfigurationType, state: StateType) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_health_readiness(self, configuration: ConfigurationType, state: StateType) -> Optional[Any]:
        pass

    @abstractmethod
    def get_capabilities(self, configuration: ConfigurationType) -> Capabilities:
        pass

    @abstractmethod
    async def get_schema(self, configuration: ConfigurationType) -> SchemaResponse:
        pass

    @abstractmethod
    async def query_explain(self,
                            configuration: ConfigurationType,
                            state: StateType,
                            request: QueryRequest) -> ExplainResponse:
        pass

    @abstractmethod
    async def mutation_explain(self,
                               configuration: ConfigurationType,
                               state: StateType,
                               request: MutationRequest) -> ExplainResponse:
        pass

    @abstractmethod
    async def mutation(self, configuration: ConfigurationType, state: StateType,
                       request: MutationRequest) -> MutationResponse:
        pass

    @abstractmethod
    async def query(self, configuration: ConfigurationType, state: StateType, request: QueryRequest) -> QueryResponse:
        pass
