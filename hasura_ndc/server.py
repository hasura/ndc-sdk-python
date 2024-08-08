from fastapi import FastAPI, Request, Depends
from fastapi.security import APIKeyHeader
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any
import uvicorn
from hasura_ndc.connector import Connector, ConfigurationType, StateType
from hasura_ndc.models import (CapabilitiesResponse, SchemaResponse, QueryResponse, ExplainResponse, MutationResponse,
                               QueryRequest, MutationRequest)
from opentelemetry import trace
import hasura_ndc.instrumentation as instrumentation
from hasura_ndc.errors import ConnectorError

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
        match_value = f"{options.service_token_secret}" if options.service_token_secret else None
        if header == match_value:
            return header
        else:
            raise HTTPException(status_code=403, detail="Invalid API Key")

    app = FastAPI(dependencies=[Depends(get_api_key)])

    @app.middleware("http")
    async def bypass_api_key_for_docs(request: Request, call_next):
        if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        await get_api_key(request.headers.get("Authorization"))
        return await call_next(request)

    @app.get("/capabilities")
    async def get_capabilities() -> CapabilitiesResponse:
        return await connector.get_capabilities(configuration)

    @app.get("/health")
    async def health_check() -> Any:
        return await connector.health_check(configuration, state)

    @app.get("/metrics")
    async def fetch_metrics() -> Any:
        return await connector.fetch_metrics(configuration, state)

    @app.get("/schema")
    async def get_schema(request: Request) -> SchemaResponse:
        return await instrumentation.with_active_span(
            tracer,
            "getSchema",
            lambda span: connector.get_schema(configuration),
            headers=dict(request.headers)
        )

    @app.post("/query")
    async def execute_query(request: Request) -> QueryResponse:
        headers = dict(request.headers)
        request_data = await request.json()
        return await instrumentation.with_active_span(
            tracer,
            "query",
            lambda span: connector.query(configuration, state, QueryRequest(**request_data)),
            headers=headers
        )

    @app.post("/query/explain")
    async def query_explain(request: Request) -> ExplainResponse:
        headers = dict(request.headers)
        request_data = await request.json()
        return await instrumentation.with_active_span(
            tracer,
            "query_explain",
            lambda span: connector.query(configuration, state, QueryRequest(**request_data)),
            headers=headers
        )

    @app.post("/mutation")
    async def execute_mutation(request: Request) -> MutationResponse:
        headers = dict(request.headers)
        request_data = await request.json()
        return await instrumentation.with_active_span(
            tracer,
            "mutation",
            lambda span: connector.mutation(configuration, state, MutationRequest(**request_data)),
            headers=headers
        )

    @app.post("/mutation/explain")
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
