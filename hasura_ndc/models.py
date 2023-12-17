from typing import Union, List, Dict, Optional, Literal, Any
from pydantic import BaseModel

OrderDirection = Literal["asc", "desc"]
RelationshipType = Literal["object", "array"]


class NamedType(BaseModel):
    type: str
    name: str


class NullableType(BaseModel):
    type: str
    underlying_type: 'Type'


class ArrayType(BaseModel):
    type: str
    element_type: 'Type'


Type = Union[NamedType, NullableType, ArrayType]


class ColumnCountAggregate(BaseModel):
    type: str
    column: str
    distinct: bool


class SingleColumnAggregate(BaseModel):
    type: str
    column: str
    function: str


class StarCountAggregate(BaseModel):
    type: str


Aggregate = Union[ColumnCountAggregate, SingleColumnAggregate, StarCountAggregate]


class ColumnField(BaseModel):
    type: str
    column: str


class RelationshipField(BaseModel):
    type: str
    query: 'Query'
    relationship: str
    arguments: Dict[str, 'RelationshipArgument']


Field = Union[ColumnField, RelationshipField]


class VariableRelationshipArgument(BaseModel):
    type: str
    name: str


class LiteralRelationshipArgument(BaseModel):
    type: str
    value: object


class ColumnRelationshipArgument(BaseModel):
    type: str
    name: str


RelationshipArgument = Union[VariableRelationshipArgument, LiteralRelationshipArgument, ColumnRelationshipArgument]


class OrderByColumn(BaseModel):
    type: str
    name: str
    path: List['PathElement']


class SingleColumnAggregateOrderBy(BaseModel):
    type: str
    column: str
    function: str
    path: List['PathElement']


class StarCountAggregateOrderBy(BaseModel):
    type: str
    path: List['PathElement']


OrderByTarget = Union[OrderByColumn, SingleColumnAggregateOrderBy, StarCountAggregateOrderBy]


class AndExpression(BaseModel):
    type: str
    expressions: List['Expression']


class OrExpression(BaseModel):
    type: str
    expressions: List['Expression']


class NotExpression(BaseModel):
    type: str
    expression: 'Expression'


class UnaryComparisonOperatorExpression(BaseModel):
    type: str
    column: 'ComparisonTarget'
    operator: 'UnaryComparisonOperator'


class BinaryComparisonOperatorExpression(BaseModel):
    type: str
    column: 'ComparisonTarget'
    operator: 'BinaryComparisonOperator'
    value: 'ComparisonValue'


class BinaryArrayComparisonOperatorExpression(BaseModel):
    type: str
    column: 'ComparisonTarget'
    operator: 'BinaryArrayComparisonOperator'
    values: List['ComparisonValue']


class ExistsExpression(BaseModel):
    type: str
    in_collection: 'ExistsInCollection'
    where: 'Expression'


Expression = Union[
    AndExpression, OrExpression, NotExpression, UnaryComparisonOperatorExpression,
    BinaryComparisonOperatorExpression, BinaryArrayComparisonOperatorExpression, ExistsExpression]


class ColumnComparisonTarget(BaseModel):
    type: str
    name: str
    path: List['PathElement']


class RootCollectionColumnComparisonTarget(BaseModel):
    type: str
    name: str


ComparisonTarget = Union[ColumnComparisonTarget, RootCollectionColumnComparisonTarget]

UnaryComparisonOperator = str  # Only 'is_null' as per the schema


class EqualBinaryComparisonOperator(BaseModel):
    type: str


class OtherBinaryComparisonOperator(BaseModel):
    type: str
    name: str


BinaryComparisonOperator = Union[EqualBinaryComparisonOperator, OtherBinaryComparisonOperator]


class ColumnComparisonValue(BaseModel):
    type: str
    column: 'ComparisonTarget'


class ScalarComparisonValue(BaseModel):
    type: str
    value: object


class VariableComparisonValue(BaseModel):
    type: str
    name: str


ComparisonValue = Union[ColumnComparisonValue, ScalarComparisonValue, VariableComparisonValue]

BinaryArrayComparisonOperator = str  # Only 'in' as per the schema


class RelatedExistsInCollection(BaseModel):
    type: str
    relationship: str
    arguments: Dict[str, 'RelationshipArgument']


class UnrelatedExistsInCollection(BaseModel):
    type: str
    collection: str
    arguments: Dict[str, 'RelationshipArgument']


ExistsInCollection = Union[RelatedExistsInCollection, UnrelatedExistsInCollection]


class VariableArgument(BaseModel):
    type: str
    name: str


class LiteralArgument(BaseModel):
    type: str
    value: object


Argument = Union[VariableArgument, LiteralArgument]


# Continuing from the previous definitions

class OrderByElement(BaseModel):
    order_direction: OrderDirection
    target: OrderByTarget


class OrderBy(BaseModel):
    elements: List[OrderByElement]


class PathElement(BaseModel):
    relationship: str
    arguments: Dict[str, RelationshipArgument]
    predicate: Expression


class Relationship(BaseModel):
    column_mapping: Dict[str, str]
    relationship_type: RelationshipType
    target_collection: str
    arguments: Dict[str, RelationshipArgument]


class RowSet(BaseModel):
    aggregates: Optional[Dict[str, object]] = None
    rows: Optional[List[Dict[str, 'RowFieldValue']]] = None


RowFieldValue = object  # Placeholder for actual field value type


class Query(BaseModel):
    aggregates: Optional[Dict[str, Aggregate]] = None
    fields: Optional[Dict[str, Field]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional[OrderBy] = None
    where: Optional[Expression] = None


class MutationOperation(BaseModel):
    type: str
    name: str
    arguments: Dict[str, object]
    fields: Optional[Dict[str, Field]] = None


class MutationRequest(BaseModel):
    operations: List[MutationOperation]
    collection_relationships: Dict[str, Relationship]


class MutationOperationResults(BaseModel):
    affected_rows: int
    returning: Optional[List[Dict[str, RowFieldValue]]] = None


class MutationResponse(BaseModel):
    operation_results: List[MutationOperationResults]


class ExplainResponse(BaseModel):
    details: Dict[str, str]


class ErrorResponse(BaseModel):
    message: str
    details: Dict[str, object]


class ValidateResponse(BaseModel):
    schema: 'SchemaResponse'
    capabilities: 'CapabilitiesResponse'
    resolved_configuration: str


class CapabilitiesResponse(BaseModel):
    versions: str
    capabilities: 'Capabilities'


class LeafCapability(BaseModel):
    pass


class Capabilities(BaseModel):
    query: 'QueryCapabilities'
    explain: Optional[LeafCapability] = None
    relationships: Optional['RelationshipCapabilities'] = None


class QueryCapabilities(BaseModel):
    aggregates: Optional[LeafCapability] = None
    variables: Optional[LeafCapability] = None


class RelationshipCapabilities(BaseModel):
    relation_comparisons: Optional[LeafCapability] = None
    order_by_aggregate: Optional[LeafCapability] = None


class SchemaResponse(BaseModel):
    scalar_types: Dict[str, 'ScalarType']
    object_types: Dict[str, 'ObjectType']
    collections: List['CollectionInfo']
    functions: List['FunctionInfo']
    procedures: List['ProcedureInfo']


class ScalarType(BaseModel):
    aggregate_functions: Dict[str, 'AggregateFunctionDefinition']
    comparison_operators: Dict[str, 'ComparisonOperatorDefinition']


class AggregateFunctionDefinition(BaseModel):
    result_type: Type


class ComparisonOperatorDefinition(BaseModel):
    argument_type: Type


class ObjectType(BaseModel):
    description: Optional[str] = None
    fields: Dict[str, 'ObjectField']


class ObjectField(BaseModel):
    description: Optional[str] = None
    type: Type


class CollectionInfo(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, 'ArgumentInfo']
    type: str
    uniqueness_constraints: Dict[str, 'UniquenessConstraint']
    foreign_keys: Dict[str, 'ForeignKeyConstraint']


class ArgumentInfo(BaseModel):
    description: Optional[str] = None
    type: Type


class UniquenessConstraint(BaseModel):
    unique_columns: List[str]


class ForeignKeyConstraint(BaseModel):
    column_mapping: Dict[str, str]
    foreign_collection: str


class FunctionInfo(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, ArgumentInfo]
    result_type: Type


class ProcedureInfo(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, ArgumentInfo]
    result_type: Type


class QueryRequest(BaseModel):
    collection: str
    query: Query
    arguments: Dict[str, Argument]
    collection_relationships: Dict[str, Relationship]
    variables: Optional[Dict[str, Any]] = None  # Replace 'Any' with the appropriate type if needed


QueryResponse = List[RowSet]  # Based on your TypeScript schema


class SchemaRoot(BaseModel):
    capabilities_response: CapabilitiesResponse
    schema_response: SchemaResponse
    query_request: QueryRequest
    query_response: QueryResponse
    mutation_request: MutationRequest
    mutation_response: MutationResponse
    explain_response: ExplainResponse
    error_response: ErrorResponse
    validate_response: ValidateResponse
