from typing import Union, List, Dict, Optional, Literal, Any
from pydantic import BaseModel

OrderDirection = Literal["asc", "desc"]
RelationshipType = Literal["object", "array"]


class RootModel(BaseModel):

    def dict(self, **kwargs):
        return super().model_dump(**kwargs, exclude_none=True)


class Type(RootModel):
    type: str
    name: Optional[str] = None
    underlying_type: Optional['Type'] = None
    element_type: Optional['Type'] = None


class Aggregate(RootModel):
    type: str
    column: Optional[str] = None
    distinct: Optional[bool] = None
    function: Optional[str] = None


class Field(RootModel):
    type: str
    column: Optional[str] = None
    query: Optional['Query'] = None
    relationship: Optional[str] = None
    arguments: Optional[Dict[str, 'RelationshipArgument']] = None


class RelationshipArgument(RootModel):
    type: str
    name: Optional[str] = None
    value: Optional[object] = None


class OrderByTarget(RootModel):
    type: str
    name: Optional[str] = None
    column: Optional[str] = None
    function: Optional[str] = None
    path: List['PathElement']


class Expression(RootModel):
    type: str
    expressions: Optional[List['Expression']] = None
    expression: Optional['Expression'] = None
    column: Optional['ComparisonTarget'] = None
    operator: Optional[
        Union['BinaryArrayComparisonOperator', 'BinaryComparisonOperator', 'UnaryComparisonOperator']] = None
    value: Optional['ComparisonValue'] = None
    values: Optional[List['ComparisonValue']] = None
    where: Optional['Expression'] = None


class ComparisonTarget(RootModel):
    type: str
    name: str
    path: Optional[List['PathElement']] = None


UnaryComparisonOperator = str  # Only 'is_null' as per the schema


class BinaryComparisonOperator(RootModel):
    type: str
    name: Optional[str] = None


class ComparisonValue(RootModel):
    type: str
    column: Optional['ComparisonTarget'] = None
    value: Optional[object] = None
    name: Optional[str] = None


BinaryArrayComparisonOperator = str  # Only 'in' as per the schema


class ExistsInCollection(RootModel):
    type: str
    relationship: Optional[str] = None
    collection: Optional[str] = None
    arguments: Dict[str, 'RelationshipArgument']


class Argument(RootModel):
    type: str
    name: Optional[str] = None
    value: Optional[object] = None


# Continuing from the previous definitions

class OrderByElement(RootModel):
    order_direction: OrderDirection
    target: OrderByTarget


class OrderBy(RootModel):
    elements: List[OrderByElement]


class PathElement(RootModel):
    relationship: str
    arguments: Dict[str, RelationshipArgument]
    predicate: Expression


class Relationship(RootModel):
    column_mapping: Dict[str, str]
    relationship_type: RelationshipType
    target_collection: str
    arguments: Dict[str, RelationshipArgument]


class RowSet(RootModel):
    aggregates: Optional[Dict[str, object]] = None
    rows: Optional[List[Dict[str, 'RowFieldValue']]] = None


RowFieldValue = object  # Placeholder for actual field value type


class Query(RootModel):
    aggregates: Optional[Dict[str, Aggregate]] = None
    fields: Optional[Dict[str, Field]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional[OrderBy] = None
    where: Optional[Expression] = None


class MutationOperation(RootModel):
    type: str
    name: str
    arguments: Dict[str, object]
    fields: Optional[Dict[str, Field]] = None


class MutationRequest(RootModel):
    operations: List[MutationOperation]
    collection_relationships: Dict[str, Relationship]


class MutationOperationResults(RootModel):
    affected_rows: int
    returning: Optional[List[Dict[str, RowFieldValue]]] = None


class MutationResponse(RootModel):
    operation_results: List[MutationOperationResults]


class ExplainResponse(RootModel):
    details: Dict[str, str]


class ErrorResponse(RootModel):
    message: str
    details: Dict[str, object]


class ValidateResponse(RootModel):
    schema: 'SchemaResponse'
    capabilities: 'CapabilitiesResponse'
    resolved_configuration: str


class CapabilitiesResponse(RootModel):
    versions: str
    capabilities: 'Capabilities'


class LeafCapability(RootModel):
    pass


class Capabilities(RootModel):
    query: 'QueryCapabilities'
    explain: Optional[LeafCapability] = None
    relationships: Optional['RelationshipCapabilities'] = None


class QueryCapabilities(RootModel):
    aggregates: Optional[LeafCapability] = None
    variables: Optional[LeafCapability] = None


class RelationshipCapabilities(RootModel):
    relation_comparisons: Optional[LeafCapability] = None
    order_by_aggregate: Optional[LeafCapability] = None


class SchemaResponse(RootModel):
    scalar_types: Dict[str, 'ScalarType']
    object_types: Dict[str, 'ObjectType']
    collections: List['CollectionInfo']
    functions: List['FunctionInfo']
    procedures: List['ProcedureInfo']


class ScalarType(RootModel):
    aggregate_functions: Dict[str, 'AggregateFunctionDefinition']
    comparison_operators: Dict[str, 'ComparisonOperatorDefinition']


class AggregateFunctionDefinition(RootModel):
    result_type: Type


class ComparisonOperatorDefinition(RootModel):
    argument_type: Type


class ObjectType(RootModel):
    description: Optional[str] = None
    fields: Dict[str, 'ObjectField']


class ObjectField(RootModel):
    description: Optional[str] = None
    type: Type


class CollectionInfo(RootModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, 'ArgumentInfo']
    type: str
    uniqueness_constraints: Dict[str, 'UniquenessConstraint']
    foreign_keys: Dict[str, 'ForeignKeyConstraint']


class ArgumentInfo(RootModel):
    description: Optional[str] = None
    type: Type


class UniquenessConstraint(RootModel):
    unique_columns: List[str]


class ForeignKeyConstraint(RootModel):
    column_mapping: Dict[str, str]
    foreign_collection: str


class FunctionInfo(RootModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, ArgumentInfo]
    result_type: Type


class ProcedureInfo(RootModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, ArgumentInfo]
    result_type: Type


class QueryRequest(RootModel):
    collection: str
    query: Query
    arguments: Dict[str, Argument]
    collection_relationships: Dict[str, Relationship]
    variables: Optional[Dict[str, Any]] = None  # Replace 'Any' with the appropriate type if needed


QueryResponse = List[RowSet]  # Based on your TypeScript schema


class SchemaRoot(RootModel):
    capabilities_response: CapabilitiesResponse
    schema_response: SchemaResponse
    query_request: QueryRequest
    query_response: QueryResponse
    mutation_request: MutationRequest
    mutation_response: MutationResponse
    explain_response: ExplainResponse
    error_response: ErrorResponse
    validate_response: ValidateResponse
