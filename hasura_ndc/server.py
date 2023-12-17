from fastapi import FastAPI, status, Request, Response, Depends
from fastapi.security import APIKeyHeader
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from typing import Any
import uvicorn
import json
from hasura_ndc.connector import Connector, RawConfigurationType, ConfigurationType, StateType
from hasura_ndc.models import (CapabilitiesResponse, SchemaResponse, QueryResponse, ExplainResponse, MutationResponse,
                               QueryRequest, MutationRequest)


class ServerOptions(BaseModel):
    configuration: str
    port: int
    service_token_secret: str
    oltp_endpoint: str
    service_name: str
    log_level: str
    pretty_print_logs: str


async def start_server(connector: Connector[RawConfigurationType, ConfigurationType, StateType],
                       options: ServerOptions):
    api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
    with open(options.configuration, "r") as f:
        raw_configuration = connector.raw_configuration_type(**json.load(f))
    configuration = await connector.validate_raw_configuration(raw_configuration)
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
    async def get_schema() -> SchemaResponse:
        return await connector.get_schema(configuration)

    @app.post("/query")
    async def execute_query(request: Request) -> QueryResponse:
        return await connector.query(configuration, state, QueryRequest(**await request.json()))

    @app.post("/explain")
    async def explain_query(request: Request) -> ExplainResponse:
        return await connector.explain(configuration, state, QueryRequest(**await request.json()))

    @app.post("/mutation")
    async def execute_mutation(request: Request) -> MutationResponse:
        return await connector.mutation(configuration, state, MutationRequest(**await request.json()))

    @app.exception_handler(Exception)
    async def http_exception_handler(_: Request, e: Exception):
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": str(e),
                "details": {}
            }
        )

    config = uvicorn.Config(app, host="0.0.0.0", port=options.port, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()
