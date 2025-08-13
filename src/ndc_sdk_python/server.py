from fastapi import FastAPI, Request, Depends
from fastapi.security import APIKeyHeader
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any
import uvicorn
from ndc_sdk_python.connector import Connector, ConfigurationType, StateType
from ndc_sdk_python.models import (CapabilitiesResponse, SchemaResponse, QueryResponse, ExplainResponse, MutationResponse,
                               QueryRequest, MutationRequest, VERSION)
from opentelemetry import trace
import ndc_sdk_python.instrumentation as instrumentation
from ndc_sdk_python.errors import ConnectorError

tracer = trace.get_tracer("ndc-sdk-python.server")


class ServerOptions(BaseModel):
    configuration: str
    port: int
    service_token_secret: str
    log_level: str
    pretty_print_logs: str


async def start_server(connector: Connector[ConfigurationType, StateType],
                       options: ServerOptions):
    api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
    configuration = await connector.parse_configuration(configuration_dir=options.configuration)
    metrics = {}
    state = await connector.try_init_state(configuration, metrics)

    async def get_api_key(header: str = Depends(api_key_header)):
        match_value = f"Bearer {options.service_token_secret}" if options.service_token_secret else None
        if header == match_value:
            return header
        else:
            raise HTTPException(status_code=403, detail="Invalid API Key")

    app = FastAPI()

    @app.get("/capabilities", dependencies=[Depends(get_api_key)])
    async def get_capabilities() -> CapabilitiesResponse:
        capabilities = await connector.get_capabilities(configuration)
        return CapabilitiesResponse(
            version=VERSION,
            capabilities=capabilities
        )

    @app.get("/health")
    async def get_health_readiness() -> Any:
        return await connector.get_health_readiness(configuration, state)

    @app.get("/metrics", dependencies=[Depends(get_api_key)])
    async def fetch_metrics() -> Any:
        return await connector.fetch_metrics(configuration, state)

    @app.get("/schema", dependencies=[Depends(get_api_key)])
    async def get_schema(request: Request) -> SchemaResponse:
        return await instrumentation.with_active_span(
            tracer,
            "getSchema",
            lambda span: connector.get_schema(configuration),
            headers=dict(request.headers)
        )

    @app.post("/query", dependencies=[Depends(get_api_key)])
    async def execute_query(request: Request) -> QueryResponse:
        headers = dict(request.headers)
        request_data = await request.json()
        return await instrumentation.with_active_span(
            tracer,
            "query",
            lambda span: connector.query(configuration, state, QueryRequest(**request_data)),
            headers=headers
        )

    @app.post("/query/explain", dependencies=[Depends(get_api_key)])
    async def query_explain(request: Request) -> ExplainResponse:
        headers = dict(request.headers)
        request_data = await request.json()
        return await instrumentation.with_active_span(
            tracer,
            "query_explain",
            lambda span: connector.query_explain(configuration, state, QueryRequest(**request_data)),
            headers=headers
        )

    @app.post("/mutation", dependencies=[Depends(get_api_key)])
    async def execute_mutation(request: Request) -> MutationResponse:
        headers = dict(request.headers)
        request_data = await request.json()
        return await instrumentation.with_active_span(
            tracer,
            "mutation",
            lambda span: connector.mutation(configuration, state, MutationRequest(**request_data)),
            headers=headers
        )

    @app.post("/mutation/explain", dependencies=[Depends(get_api_key)])
    async def mutation_explain(request: Request) -> ExplainResponse:
        headers = dict(request.headers)
        request_data = await request.json()
        return await instrumentation.with_active_span(
            tracer,
            "mutation_explain",
            lambda span: connector.mutation_explain(configuration, state, MutationRequest(**request_data)),
            headers=headers
        )

    @app.exception_handler(Exception)
    async def http_exception_handler(_: Request, e: Exception):
        if isinstance(e, ConnectorError):
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "message": str(e.message),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "message": str(e),
                    "details": {}
                }
            )

    config = uvicorn.Config(app, host=None, port=options.port, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()
