from __future__ import annotations
from typing import Union, List, Dict, Optional, Literal, Any
from pydantic import BaseModel


class RootModel(BaseModel):

    def dict(self, **kwargs):
        return super().model_dump(**kwargs, exclude_none=True)


class Type(RootModel):
    type: Literal["named", "nullable", "array", "predicate"]
    name: Optional[str] = None
    underlying_type: Optional['Type'] = None
    element_type: Optional['Type'] = None
    object_type_name: Optional[str] = None


class Aggregate(RootModel):
    type: Literal["column_count", "single_column", "star_count"]
    column: Optional[str] = None
    distinct: Optional[bool] = None
    function: Optional[str] = None


class Argument(RootModel):
    type: Literal["variable", "literal"]
    name: Optional[str] = None
    value: Optional[Any] = None


class ComparisonTarget(RootModel):
    type: Literal["column", "root_collection_column"]
    name: str
    path: Optional[List['PathElement']] = None


class ComparisonValue(RootModel):
    type: Literal["column", "scalar", "variable"]
    column: Optional['ComparisonTarget'] = None
    value: Optional[Any] = None
    name: Optional[str] = None


UnaryComparisonOperator = "is_null"


class Expression(RootModel):
    type: Literal["and", "or", "not", "unary_comparison_operator", "binary_comparison_operator", "exists"]
    expressions: Optional[List['Expression']] = None
    expression: Optional['Expression'] = None
    column: Optional['ComparisonTarget'] = None
    operator: Optional[str] = None
    value: Optional['ComparisonValue'] = None
    in_collection: Optional['ExistsInCollection'] = None
    predicate: Optional['Expression'] = None


class PathElement(RootModel):
    relationship: str
    arguments: Dict[str, 'RelationshipArgument']
    predicate: Optional['Expression'] = None


OrderDirection = Literal["asc", "desc"]


class OrderByTarget(RootModel):
    type: Literal["column", "single_column_aggregate", "star_count_aggregate"]
    name: Optional[str]
    column: Optional[str]
    function: Optional[str]
    path: List['PathElement']


class OrderBy(RootModel):
    elements: List['OrderByElement']


class OrderByElement(RootModel):
    order_direction: 'OrderDirection'
    target: 'OrderByTarget'


class Query(RootModel):
    aggregates: Optional[Dict[str, 'Aggregate']] = None
    fields: Optional[Dict[str, 'Field']] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional['OrderBy'] = None
    predicate: Optional['Expression'] = None


class RelationshipArgument(RootModel):
    type: Literal["variable", "literal", "column"]
    name: Optional[str] = None
    value: Optional[Any] = None


class NestedField(RootModel):
    type: Literal["object", "array"]
    fields: Union[Dict[str, 'Field'], 'NestedField']


class Field(RootModel):
    type: Literal["column", "relationship"]
    column: Optional[str] = None
    fields: Optional['NestedField'] = None
    query: Optional['Query'] = None
    relationship: Optional[str] = None
    arguments: Optional[Dict[str, 'RelationshipArgument']] = None


class ExistsInCollection(RootModel):
    type: Literal["related", "unrelated"]
    relationship: Optional[str] = None
    collection: Optional[str] = None
    arguments: Dict[str, 'RelationshipArgument']


RelationshipType = Literal["object", "array"]


class RowSet(RootModel):
    aggregates: Optional[Dict[str, Any]] = None
    rows: Optional[List[Dict[str, Any]]] = None


QueryResponse = List[RowSet]


class Relationship(RootModel):
    column_mapping: Dict[str, str]
    relationship_type: 'RelationshipType'
    target_collection: str
    arguments: Dict[str, 'RelationshipArgument']


class MutationOperation(RootModel):
    type: Literal["procedure"]
    name: str
    arguments: Dict[str, Any]
    fields: Optional['NestedField'] = None


class MutationOperationResults(RootModel):
    type: Literal["procedure"]
    result: Any


class CapabilitiesResponse(RootModel):
    version: str
    capabilities: 'Capabilities'


class Capabilities(RootModel):
    query: 'QueryCapabilities'
    mutation: 'MutationCapabilities'
    relationships: Optional['RelationshipCapabilities'] = None


class SchemaRoot(RootModel):
    capabilities_response: CapabilitiesResponse
    schema_response: 'SchemaResponse'
    query_request: 'QueryRequest'
    query_response: 'QueryResponse'
    mutation_request: 'MutationRequest'
    mutation_response: 'MutationResponse'
    explain_response: 'ExplainResponse'
    error_response: 'ErrorResponse'
    validate_response: 'ValidateResponse'


class LeafCapability(RootModel):
    pass


class QueryCapabilities(RootModel):
    aggregates: Optional['LeafCapability'] = None
    variables: Optional['LeafCapability'] = None
    explain: Optional['LeafCapability'] = None


class MutationCapabilities(RootModel):
    transactional: Optional['LeafCapability'] = None
    explain: Optional['LeafCapability'] = None


class RelationshipCapabilities(RootModel):
    relation_comparisons: Optional['LeafCapability'] = None
    order_by_aggregate: Optional['LeafCapability'] = None


class SchemaResponse(RootModel):
    scalar_types: Dict[str, 'ScalarType']
    object_types: Dict[str, 'ObjectType']
    collections: List['CollectionInfo']
    functions: List['FunctionInfo']
    procedures: List['ProcedureInfo']


class TypeRepresentation(RootModel):
    type: Literal[
        "boolean", "string", "number", "integer", "int8", "int16", "int32", "int64", "float32", "float64", "bigdecimal",
        "uuid", "date", "timestamp", "timestamptz", "geography", "geometry", "bytes", "json", "enum"]
    one_of: Optional[List[str]] = None


class ComparisonOperatorDefinition(RootModel):
    type: Literal["equal", "in", "custom"]
    argument_type: Optional['Type'] = None


class ScalarType(RootModel):
    representation: Optional['TypeRepresentation'] = None
    aggregate_functions: Dict[str, 'AggregateFunctionDefinition']
    comparison_operators: Dict[str, 'ComparisonOperatorDefinition']


class AggregateFunctionDefinition(RootModel):
    result_type: 'Type'


class ObjectType(RootModel):
    description: Optional[str] = None
    fields: Dict[str, 'ObjectField']


class ObjectField(RootModel):
    description: Optional[str] = None
    type: 'Type'


class CollectionInfo(RootModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, 'ArgumentInfo']
    type: str
    uniqueness_constraints: Dict[str, 'UniquenessConstraint']
    foreign_keys: Dict[str, 'ForeignKeyConstraint']


class ArgumentInfo(RootModel):
    description: Optional[str] = None
    type: 'Type'


class UniquenessConstraint(RootModel):
    unique_columns: List[str]


class ForeignKeyConstraint(RootModel):
    column_mapping: Dict[str, str]
    foreign_collection: str


class FunctionInfo(RootModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, 'ArgumentInfo']
    result_type: 'Type'


class ProcedureInfo(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, 'ArgumentInfo']
    result_type: 'Type'


class QueryRequest(BaseModel):
    collection: str
    query: 'Query'
    arguments: Dict[str, 'Argument']
    collection_relationships: Dict[str, 'Relationship']
    variables: Optional[Dict[str, Any]] = None


class MutationRequest(BaseModel):
    operations: List['MutationOperation']
    collection_relationships: Dict[str, 'Relationship']


class MutationResponse(BaseModel):
    operation_results: List['MutationOperationResults']


class ExplainResponse(BaseModel):
    details: Dict[str, str]


class ErrorResponse(BaseModel):
    message: str
    details: Dict[str, Any]


class ValidateResponse(BaseModel):
    schema: SchemaResponse
    capabilities: CapabilitiesResponse
    resolved_configuration: str
