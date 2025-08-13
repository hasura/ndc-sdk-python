import os
import argparse
import asyncio
from ndc_sdk_python.connector import *
from ndc_sdk_python.server import start_server
import ndc_sdk_python.instrumentation as instrumentation

if not instrumentation.is_initialized():
    instrumentation.init_telemetry()


async def start_server_wrapper(connector, args):
    args.configuration = os.getenv('HASURA_CONFIGURATION_DIRECTORY', args.configuration)
    args.port = int(os.getenv('HASURA_CONNECTOR_PORT', args.port))
    args.service_token_secret = os.getenv('HASURA_SERVICE_TOKEN_SECRET', args.service_token_secret)
    args.log_level = os.getenv('HASURA_LOG_LEVEL', args.log_level)
    args.pretty_print_logs = bool(os.getenv('HASURA_PRETTY_PRINT_LOGS', args.pretty_print_logs))
    await start_server(connector, args)


def start(connector: Connector):
    parser = argparse.ArgumentParser(description='Connector CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    serve_parser = subparsers.add_parser('serve', help='Start the server')
    _add_serve_command_arguments(serve_parser)
    serve_parser.set_defaults(func=start_server_wrapper)

    args = parser.parse_args()
    asyncio.run(args.func(connector, args))


def _add_serve_command_arguments(parser):
    # Setting defaults to None to allow for checks later
    parser.add_argument('--configuration', default=None, help='Path to the configuration file')
    parser.add_argument('--port', type=int, default=8080, help='Port number')
    parser.add_argument('--service-token-secret', default=None, help='Service token secret')
    parser.add_argument('--log-level', default='info', help='Logging level')
    parser.add_argument('--pretty-print-logs', default=False, help="Pretty print logs")
