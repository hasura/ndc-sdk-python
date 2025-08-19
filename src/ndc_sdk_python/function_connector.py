from ndc_sdk_python.connector import Connector
from ndc_sdk_python.main import start
from ndc_sdk_python.models import *
from pydantic import BaseModel
import inspect
import asyncio
from typing import Optional, get_origin, get_args, Union
import types

class HeaderMap(dict):
    pass


class Configuration(BaseModel):
    pass


class State(BaseModel):
    pass


class FunctionConnector(Connector[Configuration, State]):

    def __init__(self):
        super().__init__(Configuration, State)
        self.query_functions = {}
        self.mutation_functions = {}

    async def parse_configuration(self, configuration_dir: str) -> Configuration:
        config = Configuration()
        return config

    async def try_init_state(self, configuration: Configuration, metrics: Any) -> State:
        return State()

    async def get_capabilities(self, configuration: Configuration) -> Capabilities:
        return Capabilities(
                query=QueryCapabilities(
                    aggregates=LeafCapability(),
                    variables=LeafCapability(),
                    explain=LeafCapability(),
                    nested_fields=NestedFieldCapabilities(),
                    exists=ExistsCapabilities()
                ),
                mutation=MutationCapabilities(
                    transactional=LeafCapability(),
                    explain=None
                )
            )

    async def query_explain(self,
                            configuration: Configuration,
                            state: State,
                            request: QueryRequest) -> ExplainResponse:
        pass

    async def mutation_explain(self,
                               configuration: Configuration,
                               state: State,
                               request: MutationRequest) -> ExplainResponse:
        pass

    async def fetch_metrics(self,
                            configuration: Configuration,
                            state: State) -> Optional[None]:
        pass

    async def get_health_readiness(self,
                           configuration: Configuration,
                           state: State) -> Optional[None]:
        pass

    async def get_schema(self, configuration: Configuration) -> SchemaResponse:
        functions = []
        procedures = []
        scalar_types = {
                "String": ScalarType(
                    representation=StringType(type="string"),
                    aggregate_functions={},
                    comparison_operators={}
                ),
                "Int": ScalarType(
                    representation=IntegerType(type="integer"),
                    aggregate_functions={},
                    comparison_operators={}
                ),
                "Float": ScalarType(
                    representation=Float64Type(type="float64"),
                    aggregate_functions={},
                    comparison_operators={}
                ),
                "Boolean": ScalarType(
                    representation=BooleanType(type="boolean"),
                    aggregate_functions={},
                    comparison_operators={}
                ),
                "Json": ScalarType(
                    representation=JsonType(type="json"),
                    aggregate_functions={},
                    comparison_operators={}
                ),
                "HeaderMap": ScalarType(
                    representation=JsonType(type="json"),
                    aggregate_functions={},
                    comparison_operators={}
                )
            }
        object_types = {}
        for name, (func, _parallel_degree) in self.query_functions.items():
            function_info = self.generate_function_info(name, func, object_types)
            functions.append(function_info)

        for name, func in self.mutation_functions.items():
            procedure_info = self.generate_procedure_info(name, func, object_types)
            procedures.append(procedure_info)

        schema_response = SchemaResponse(
            scalar_types=scalar_types,
            functions=functions,
            procedures=procedures,
            object_types=object_types,
            collections=[]
        )

        return schema_response

    def generate_function_info(self, name, func, object_types):
        signature = inspect.signature(func)
        arguments = {}
        for arg_name, arg_type in signature.parameters.items():
            if arg_type.annotation != HeaderMap:

                arg_description = None
                if arg_type.default != inspect.Parameter.empty:
                    if hasattr(arg_type.default, 'description'):
                        arg_description = arg_type.default.description
      
                if arg_description is None:
                    origin = get_origin(arg_type.annotation)
                    if origin is Annotated:
                        args = get_args(arg_type.annotation)
                        # Look for string descriptions in the metadata
                        for arg in args[1:]:
                            if isinstance(arg, str):
                                arg_description = arg
                                break

                arguments[arg_name] = {
                    "type": self.get_type_info(arg_type, name, object_types, arg_name),
                    "description": arg_description
                }
        
        description = None
        if func.__doc__:
            description = func.__doc__.strip()

        return FunctionInfo(
            name=name,
            arguments=arguments,
            result_type=self.get_type_info(signature.return_annotation, name, object_types, None),
            description=description
        )

    def generate_procedure_info(self, name, func, object_types):
        signature = inspect.signature(func)
        arguments = {}
        for arg_name, arg_type in signature.parameters.items():
            if arg_type.annotation != HeaderMap:

                arg_description = None

                if arg_type.default != inspect.Parameter.empty:
                    if hasattr(arg_type.default, 'description'):
                        arg_description = arg_type.default.description

                if arg_description is None:
                    origin = get_origin(arg_type.annotation)
                    if origin is Annotated:
                        args = get_args(arg_type.annotation)
                        # Look for string descriptions in the metadata
                        for arg in args[1:]:
                            if isinstance(arg, str):
                                arg_description = arg
                                break

                arguments[arg_name] = {
                    "type": self.get_type_info(arg_type, name, object_types, arg_name),
                    "description": arg_description
                }

        description = None
        if func.__doc__:
            description = func.__doc__.strip()
        
        return ProcedureInfo(
            name=name,
            arguments=arguments,
            result_type=self.get_type_info(signature.return_annotation, name, object_types, None),
            description=description
        )

    @staticmethod
    def get_type_info(typ, caller_name, object_types, arg_name=None):
        if isinstance(typ, inspect.Parameter):
            typ = typ.annotation

        origin = get_origin(typ)
        if origin is Annotated:
            args = get_args(typ)
            if args:
                typ = args[0]

        # If the type is an array we should return a ArrayType with the underlying type
        if typ == int:
            res = NamedType(type="named", name="Int")
        elif typ == float:
            res = NamedType(type="named", name="Float")
        elif typ == str:
            res = NamedType(type="named", name="String")
        elif typ == bool:
            res = NamedType(type="named", name="Boolean")
        elif typ == inspect._empty:
            res = NamedType(type="named", name="Json")
        elif typ == list or get_origin(typ) == list:
            if typ == list:
                res = ArrayType(type="array", element_type=NamedType(type="named", name="Json"))              
            elif len(typ.__args__) == 0:
                res = ArrayType(type="array", element_type=NamedType(type="named", name="Json"))
            else:
                model_name = f"{caller_name}"
                if arg_name:
                    model_name = f"{caller_name}_{arg_name}"
                res = ArrayType(type="array", element_type=FunctionConnector.get_type_info(typ.__args__[0], model_name, object_types, None))
        elif get_origin(typ) in (Union, types.UnionType) and type(None) in get_args(typ):
            args = get_args(typ)
            non_none_types = [t for t in args if t != type(None)]
            if len(non_none_types) == 1:
                model_name = f"{caller_name}"
                if arg_name:
                    model_name = f"{caller_name}_{arg_name}"
                res = NullableType(type="nullable", underlying_type=FunctionConnector.get_type_info(non_none_types[0], model_name, object_types, None))
            else:
                res = NullableType(type="nullable", underlying_type=NamedType(type="named", name="Json"))
        elif issubclass(typ, BaseModel):
            model_name = f"{caller_name}"
            if arg_name:
                model_name = f"{caller_name}_{arg_name}"
            if model_name not in object_types:
                fields = {}
                for name, field in typ.model_fields.items():
                    field_type = FunctionConnector.get_type_info(field.annotation, model_name, object_types, name)
                    
                    field_description = field.description
                    if not field_description:
                        original_annotation = typ.__annotations__.get(name)
                        if original_annotation:
                            field_origin = get_origin(original_annotation)
                            if field_origin is Annotated:
                                field_args = get_args(original_annotation)
                                for arg in field_args[1:]:
                                    if isinstance(arg, str):
                                        field_description = arg
                                        break

                    fields[name] = ObjectField(
                        type=field_type,
                        description=field_description,
                        arguments={}
                    )
                object_types[model_name] = ObjectType(
                    description=typ.__doc__,
                    fields=fields
                )
            res = NamedType(type="named", name=model_name)
        else:
            res = NamedType(type="named", name="Json")
        return res

    @staticmethod
    def reshape_result(result, requested_fields):
        def reshape_value(value, fields):
            if value is None:
                return None

            if isinstance(fields, NestedArray):
                if isinstance(value, list):
                    return [reshape_value(item, fields.fields) for item in value]
                else:
                    return reshape_value(value, fields.fields)
            elif isinstance(fields, NestedObject):
                return reshape_object(value, fields.fields)
            elif isinstance(fields, ColumnField):
                if fields.fields:
                    return reshape_value(getattr(value, fields.column), fields.fields)
                else:
                    return getattr(value, fields.column)
            else:
                return value

        def reshape_object(obj, fields):
            if obj is None:
                return None

            reshaped = {}
            for field_alias, field in fields.items():
                if isinstance(field, ColumnField):
                    value = getattr(obj, field.column)
                    if field.fields:
                        reshaped[field_alias] = reshape_value(value, field.fields)
                    else:
                        reshaped[field_alias] = value
                elif isinstance(field, (NestedObject, NestedArray)):
                    reshaped[field_alias] = reshape_value(getattr(obj, field_alias), field)
            return reshaped

        return reshape_value(result, requested_fields)

    @staticmethod
    def cast_to_type(value, target_type):
        origin = get_origin(target_type)
        if origin == types.UnionType:
            args = get_args(target_type)
            if types.NoneType in args and len(args) == 2:
                # target type is just a nullable type
                if value is None:
                    return None
                other_type = next(t for t in args if t is not types.NoneType)
                return FunctionConnector.cast_to_type(value, other_type)
        elif origin == list:
            args = get_args(target_type)
            if len(args) == 1:
                element_type = args[0]
                return [FunctionConnector.cast_to_type(item, element_type) for item in value]
            else:
                return value  # If it's List without type argument, return as is
        elif origin is not None and issubclass(origin, BaseModel):
            return origin(**value)
        elif inspect.isclass(target_type) and issubclass(target_type, BaseModel):
            return target_type(**value)
        else:
            return value


    async def query(self, configuration: Configuration, state: State, request: QueryRequest) -> QueryResponse:
        func, parallel_degree = self.query_functions[request.collection]
        signature = inspect.signature(func)
        
        root_args = {}
        root_vars = {}
        for k, v in request.arguments.items():
            if v.type == "literal":
                arg_type = signature.parameters[k].annotation
                if isinstance(arg_type, type) or (get_origin(arg_type) is not None):
                    root_args[k] = self.cast_to_type(v.value, arg_type)
                else:
                    root_args[k] = v.value
            elif v.type == "variable":
                root_vars[k] = v.name

        args_array = []
        if request.variables:
            for var in request.variables:
                var_args = {}
                for var_key, var_name in root_vars.items():
                    arg_type = signature.parameters[var_key].annotation
                    var_args[var_key] = self.cast_to_type(var[var_name], arg_type)
                args_array.append({
                    **var_args,
                    **root_args
                })
        else:
            args_array = [root_args]


        async def process_args(args):
            if asyncio.iscoroutinefunction(func):
                result = await func(**args)
            else:
                result = func(**args)

            reshaped_result = FunctionConnector.reshape_result(result, request.query.fields["__value"].fields)
            
            return RowSet(
                aggregates=None,
                rows=[
                    {"__value": reshaped_result}
                ]
            )

        async def process_batch(batch):
            return await asyncio.gather(*[process_args(args) for args in batch])

        row_sets = []
        for i in range(0, len(args_array), parallel_degree):
            batch = args_array[i:i + parallel_degree]
            batch_results = await process_batch(batch)
            row_sets.extend(batch_results)

        return row_sets

    async def mutation(self, 
                       configuration: Configuration,
                       state: State,
                       request: MutationRequest) -> MutationResponse:
        responses = []
        for operation in request.operations:
            operation_name = operation.name
            func = self.mutation_functions[operation_name]
            signature = inspect.signature(func)
            args = {}
            if operation.arguments:
                for k, v in operation.arguments.items():
                    arg_type = signature.parameters[k].annotation
                    args[k] = self.cast_to_type(v, arg_type)
            if asyncio.iscoroutinefunction(func):
                response = await func(**args)
            else:
                response = func(**args)
            reshaped_response = FunctionConnector.reshape_result(response, operation.fields)
            responses.append(reshaped_response)
        return MutationResponse(
            operation_results=[
                MutationOperationResults(
                    type="procedure",
                    result=response
                ) for response in responses
            ]
        )

    def register_query(self, func=None, *, parallel_degree=1):
        
        def decorator(f):
            self.query_functions[f.__name__] = (f, parallel_degree)
            return f
        
        if func is None:
            return decorator
        else:
            return decorator(func)

    def register_mutation(self, func):
        self.mutation_functions[func.__name__] = func
        return func
