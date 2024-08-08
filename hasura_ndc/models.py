from __future__ import annotations
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel
from pydantic import Field as PydanticField
from typing_extensions import Annotated
import warnings

warnings.filterwarnings("ignore", message="Field name .* shadows an attribute in parent .*")


class RootModel(BaseModel):

    def dict(self, **kwargs):
        return super().model_dump(**kwargs, exclude_none=True)

# class TypeRepresentation(RootModel):
#     type: Literal[
#         "boolean", "string", "number", "integer", "int8", "int16", "int32", "int64", "float32", "float64", "bigdecimal",
#         "uuid", "date", "timestamp", "timestamptz", "geography", "geometry", "bytes", "json", "enum"]
#     one_of: Optional[List[str]] = None

class BooleanType(RootModel):
    type: Literal["boolean"]

class StringType(RootModel):
    type: Literal["string"]

class NumberType(RootModel):
    type: Literal["number"]

class IntegerType(RootModel):
    type: Literal["integer"]

class Int8Type(RootModel):
    type: Literal["int8"]

class Int16Type(RootModel):
    type: Literal["int16"]

class Int32Type(RootModel):
    type: Literal["int32"]

class Int64Type(RootModel):
    type: Literal["int64"]

class Float32Type(RootModel):
    type: Literal["float32"]

class Float64Type(RootModel):
    type: Literal["float64"]

class BigIntegerType(RootModel):
    type: Literal["biginteger"]

class BigDecimalType(RootModel):
    type: Literal["bigdecimal"]

class UUIDType(RootModel):
    type: Literal["uuid"]

class DateType(RootModel):
    type: Literal["date"]

class TimestampType(RootModel):
    type: Literal["timestamp"]

class TimestamptzType(RootModel):
    type: Literal["timestamptz"]

class GeographyType(RootModel):
    type: Literal["geography"]

class GeometryType(RootModel):
    type: Literal["geometry"]

class BytesType(RootModel):
    type: Literal["bytes"]

class JsonType(RootModel):
    type: Literal["json"]

class EnumType(RootModel):
    type: Literal["enum"]
    one_of: List[str]

TypeRepresentation = Annotated[
    BooleanType | StringType | NumberType | IntegerType | Int8Type | Int16Type | Int32Type | Int64Type |
    Float32Type | Float64Type | BigIntegerType | BigDecimalType | UUIDType | DateType | TimestampType |
    TimestamptzType | GeographyType | GeometryType | BytesType | JsonType | EnumType,
    PydanticField(discriminator='type')
]

# class Type(RootModel):
#     type: Literal["named", "nullable", "array", "predicate"]
#     name: Optional[str] = None
#     underlying_type: Optional['Type'] = None
#     element_type: Optional['Type'] = None
#     object_type_name: Optional[str] = None

class NamedType(RootModel):
    type: Literal["named"]
    name: str

class NullableType(RootModel):
    type: Literal["nullable"]
    underlying_type: 'Type'

class ArrayType(RootModel):
    type: Literal["array"]
    element_type: 'Type'

class PredicateType(RootModel):
    type: Literal["predicate"]
    object_type_name: str

Type = Annotated[
    NamedType | NullableType | ArrayType | PredicateType,
    PydanticField(discriminator='type')
]

# class Aggregate(RootModel):
#     type: Literal["column_count", "single_column", "star_count"]
#     column: Optional[str] = None
#     distinct: Optional[bool] = None
#     function: Optional[str] = None

class ColumnCountType(RootModel):
    type: Literal["column_count"]
    column: str
    field_path: Optional[List[str]] = None
    distinct: bool

class SingleColumnType(RootModel):
    type: Literal["single_column"]
    column: str
    field_path: Optional[List[str]] = None
    function: str

class StarCountType(RootModel):
    type: Literal["star_count"]

Aggregate = Annotated[
    ColumnCountType | SingleColumnType | StarCountType,
    PydanticField(discriminator='type')
]


# class Argument(RootModel):
#     type: Literal["variable", "literal"]
#     name: Optional[str] = None
#     value: Optional[Any] = None

class VariableArgument(RootModel):
    type: Literal["variable"]
    name: str

class LiteralArgument(RootModel):
    type: Literal["literal"]
    value: Any

Argument = Annotated[
    VariableArgument | LiteralArgument,
    PydanticField(discriminator='type')
]


# class ComparisonTarget(RootModel):
#     type: Literal["column", "root_collection_column"]
#     name: str
#     path: Optional[List['PathElement']] = None

class ColumnTarget(RootModel):
    type: Literal["column"]
    name: str
    field_path: Optional[List[str]] = None
    path: List['PathElement']

class RootCollectionColumnTarget(RootModel):
    type: Literal["root_collection_column"]
    name: str
    field_path: Optional[List[str]] = None

ComparisonTarget = Annotated[
    ColumnTarget | RootCollectionColumnTarget,
    PydanticField(discriminator='type')
]


# class ComparisonValue(RootModel):
#     type: Literal["column", "scalar", "variable"]
#     column: Optional['ComparisonTarget'] = None
#     value: Optional[Any] = None
#     name: Optional[str] = None

class ColumnValue(RootModel):
    type: Literal["column"]
    column: 'ComparisonTarget'  # Forward reference to ComparisonTarget

class ScalarValue(RootModel):
    type: Literal["scalar"]
    value: Any

class VariableValue(RootModel):
    type: Literal["variable"]
    name: str

ComparisonValue = Annotated[
    ColumnValue | ScalarValue | VariableValue,
    PydanticField(discriminator='type')
]


# UnaryComparisonOperator = "is_null"
UnaryComparisonOperator = Literal["is_null"]

# class Expression(RootModel):
#     type: Literal["and", "or", "not", "unary_comparison_operator", "binary_comparison_operator", "exists"]
#     expressions: Optional[List['Expression']] = None
#     expression: Optional['Expression'] = None
#     column: Optional['ComparisonTarget'] = None
#     operator: Optional[str] = None
#     value: Optional['ComparisonValue'] = None
#     in_collection: Optional['ExistsInCollection'] = None
#     predicate: Optional['Expression'] = None

class AndExpression(RootModel):
    type: Literal["and"]
    expressions: List['Expression']

class OrExpression(RootModel):
    type: Literal["or"]
    expressions: List['Expression']

class NotExpression(RootModel):
    type: Literal["not"]
    expression: 'Expression'

class UnaryComparisonOperatorExpression(RootModel):
    type: Literal["unary_comparison_operator"]
    column: 'ComparisonTarget'
    operator: 'UnaryComparisonOperator'

class BinaryComparisonOperatorExpression(RootModel):
    type: Literal["binary_comparison_operator"]
    column: 'ComparisonTarget'
    operator: str
    value: 'ComparisonValue'

class ExistsExpression(RootModel):
    type: Literal["exists"]
    in_collection: 'ExistsInCollection'
    predicate: Optional['Expression'] = None

Expression = Annotated[
    AndExpression | OrExpression | NotExpression | UnaryComparisonOperatorExpression | BinaryComparisonOperatorExpression | ExistsExpression,
    PydanticField(discriminator='type')
]


class PathElement(RootModel):
    relationship: str
    arguments: Dict[str, 'RelationshipArgument']
    predicate: Optional['Expression'] = None


OrderDirection = Literal["asc", "desc"]

# class OrderByTarget(RootModel):
#     type: Literal["column", "single_column_aggregate", "star_count_aggregate"]
#     name: Optional[str]
#     column: Optional[str]
#     function: Optional[str]
#     path: List['PathElement']

class ColumnOrderByTarget(RootModel):
    type: Literal["column"]
    name: str
    field_path: Optional[List[str]] = None
    path: List[PathElement]

class SingleColumnAggregateOrderByTarget(RootModel):
    type: Literal["single_column_aggregate"]
    column: str
    field_path: Optional[List[str]] = None
    function: str
    path: List[PathElement]

class StarCountAggregateOrderByTarget(RootModel):
    type: Literal["star_count_aggregate"]
    path: List[PathElement]

OrderByTarget = Annotated[
    ColumnOrderByTarget | SingleColumnAggregateOrderByTarget | StarCountAggregateOrderByTarget,
    PydanticField(discriminator='type')
]


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


# class RelationshipArgument(RootModel):
#     type: Literal["variable", "literal", "column"]
#     name: Optional[str] = None
#     value: Optional[Any] = None
    
class VariableRelationshipArgument(RootModel):
    type: Literal["variable"]
    name: str

class LiteralRelationshipArgument(RootModel):
    type: Literal["literal"]
    value: Any

class ColumnRelationshipArgument(RootModel):
    type: Literal["column"]
    name: str

RelationshipArgument = Annotated[
    VariableRelationshipArgument | LiteralRelationshipArgument | ColumnRelationshipArgument,
    PydanticField(discriminator='type')
]


# class NestedField(RootModel):
#     type: Literal["object", "array"]
#     fields: Union[Dict[str, 'Field'], 'NestedField']

class NestedObject(RootModel):
    type: Literal["object"]
    fields: Dict[str, Field]

class NestedArray(RootModel):
    type: Literal["array"]
    fields: 'NestedField'  # Forward reference to NestedField

NestedField = Annotated[
    NestedObject | NestedArray,
    PydanticField(discriminator='type')
]


# class Field(RootModel):
#     type: Literal["column", "relationship"]
#     column: Optional[str] = None
#     fields: Optional['NestedField'] = None
#     query: Optional['Query'] = None
#     relationship: Optional[str] = None
#     arguments: Optional[Dict[str, 'RelationshipArgument']] = None

class ColumnField(RootModel):
    type: Literal["column"]
    column: str
    fields: Optional['NestedField'] = None
    arguments: Optional[Dict[str, 'Argument']] = None

class RelationshipField(RootModel):
    type: Literal["relationship"]
    query: 'Query'
    relationship: str
    arguments: Dict[str, 'RelationshipArgument']

Field = Annotated[
    ColumnField | RelationshipField,
    PydanticField(discriminator='type')
]


# class ExistsInCollection(RootModel):
#     type: Literal["related", "unrelated"]
#     relationship: Optional[str] = None
#     collection: Optional[str] = None
#     arguments: Dict[str, 'RelationshipArgument']

class RelatedExistsInCollection(RootModel):
    type: Literal["related"]
    relationship: str
    arguments: Dict[str, 'RelationshipArgument']

class UnrelatedExistsInCollection(RootModel):
    type: Literal["unrelated"]
    collection: str
    arguments: Dict[str, 'RelationshipArgument']

ExistsInCollection = Annotated[
    RelatedExistsInCollection | UnrelatedExistsInCollection,
    PydanticField(discriminator='type')
]

RelationshipType = Literal["object", "array"]

RowFieldValue = Any

class RowSet(RootModel):
    aggregates: Optional[Dict[str, Any]] = None
    rows: Optional[List[Dict[str, RowFieldValue]]] = None


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

class NestedFieldCapabilities(RootModel):
    filter_by: Optional['LeafCapability'] = None
    order_by: Optional['LeafCapability'] = None
    aggregates: Optional['LeafCapability'] = None

class QueryCapabilities(RootModel):
    aggregates: Optional['LeafCapability'] = None
    variables: Optional['LeafCapability'] = None
    explain: Optional['LeafCapability'] = None
    nested_fields: Optional['NestedFieldCapabilities'] = None


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


# class ComparisonOperatorDefinition(RootModel):
#     type: Literal["equal", "in", "custom"]
#     argument_type: Optional['Type'] = None

class EqualOperator(RootModel):
    type: Literal["equal"]

class InOperator(RootModel):
    type: Literal["in"]

class CustomOperator(RootModel):
    type: Literal["custom"]
    argument_type: Optional['Type']

ComparisonOperatorDefinition = Annotated[
    EqualOperator | InOperator | CustomOperator,
    PydanticField(discriminator='type')
]


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
    arguments: Optional[Dict[str, 'ArgumentInfo']] = None


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


class ProcedureInfo(RootModel):
    name: str
    description: Optional[str] = None
    arguments: Dict[str, 'ArgumentInfo']
    result_type: 'Type'


class QueryRequest(RootModel):
    collection: str
    query: 'Query'
    arguments: Dict[str, 'Argument']
    collection_relationships: Dict[str, 'Relationship']
    variables: Optional[List[Dict[str, Any]]] = None


class MutationRequest(RootModel):
    operations: List['MutationOperation']
    collection_relationships: Dict[str, 'Relationship']


class MutationResponse(RootModel):
    operation_results: List['MutationOperationResults']


class ExplainResponse(RootModel):
    details: Dict[str, str]


class ErrorResponse(RootModel):
    message: str
    details: Dict[str, Any]


class ValidateResponse(RootModel):
    schema: SchemaResponse
    capabilities: CapabilitiesResponse
    resolved_configuration: str

VERSION = "0.1.5"