from typing import Generic, TypeVar, Any, Dict
from typing import Optional
from abc import ABC, abstractmethod
from hasura_ndc.models import (
    CapabilitiesResponse,
    SchemaResponse,
    QueryRequest,
    QueryResponse,
    ExplainResponse,
    MutationRequest,
    MutationResponse
)
from pydantic import BaseModel

# Define type variables for RawConfiguration, Configuration, and State
RawConfigurationType = TypeVar('RawConfigurationType', bound=BaseModel)
ConfigurationType = TypeVar('ConfigurationType', bound=BaseModel)
StateType = TypeVar('StateType', bound=BaseModel)


class Connector(ABC, Generic[RawConfigurationType, ConfigurationType, StateType]):

    def __init__(self, raw_configuration_type, configuration_type, state_type):
        self.raw_configuration_type = raw_configuration_type
        self.configuration_type = configuration_type
        self.state_type = state_type

    @abstractmethod
    def get_raw_configuration_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def make_empty_configuration(self) -> RawConfigurationType:
        pass

    @abstractmethod
    async def update_configuration(self, raw_configuration: RawConfigurationType) -> RawConfigurationType:
        pass

    @abstractmethod
    async def validate_raw_configuration(self, raw_configuration: RawConfigurationType) -> ConfigurationType:
        pass

    @abstractmethod
    async def try_init_state(self, configuration: ConfigurationType, metrics: Any) -> StateType:
        pass

    @abstractmethod
    async def fetch_metrics(self, configuration: ConfigurationType, state: StateType) -> Optional[None]:
        pass

    @abstractmethod
    async def health_check(self, configuration: ConfigurationType, state: StateType) -> Optional[None]:
        pass

    @abstractmethod
    def get_capabilities(self, configuration: ConfigurationType) -> CapabilitiesResponse:
        pass

    @abstractmethod
    async def get_schema(self, configuration: ConfigurationType) -> SchemaResponse:
        pass

    @abstractmethod
    async def explain(self, configuration: ConfigurationType, state: StateType,
                      request: QueryRequest) -> ExplainResponse:
        pass

    @abstractmethod
    async def mutation(self, configuration: ConfigurationType, state: StateType,
                       request: MutationRequest) -> MutationResponse:
        pass

    @abstractmethod
    async def query(self, configuration: ConfigurationType, state: StateType, request: QueryRequest) -> QueryResponse:
        pass
