from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict
import uvicorn
from hasura_ndc.connector import Connector
from hasura_ndc.models import ValidateResponse


class ConfigurationServerOptions(BaseModel):
    port: int
    log_level: str
    pretty_print_logs: bool


async def start_configuration_server(connector: Connector, options: ConfigurationServerOptions):
    app = FastAPI()

    @app.get("/")
    async def get_schema(_: Request):
        return connector.make_empty_configuration()

    @app.post("/")
    async def update_configuration(request: Request):
        raw_configuration = connector.raw_configuration_type(**await request.json())
        return await connector.update_configuration(raw_configuration)

    @app.get("/schema")
    async def get_raw_configuration_schema() -> Dict[str, Any]:
        return connector.get_raw_configuration_schema()

    @app.post("/validate")
    async def validate_configuration(request: Request) -> ValidateResponse:
        raw_configuration = connector.raw_configuration_type(**await request.json())
        resolved_configuration = await connector.validate_raw_configuration(raw_configuration)
        schema = await connector.get_schema(resolved_configuration)
        capabilities = connector.get_capabilities(resolved_configuration)
        return ValidateResponse(
            schema=schema,
            capabilities=capabilities,
            resolved_configuration=resolved_configuration
        )

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.detail,
                "details": {}
            },
        )

    config = uvicorn.Config(app, host="0.0.0.0", port=options.port, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()
