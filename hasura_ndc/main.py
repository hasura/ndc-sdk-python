import argparse
import asyncio
from hasura_ndc.connector import *
from hasura_ndc.server import start_server
from hasura_ndc.configuration_server import start_configuration_server


async def start_server_wrapper(connector, args):
    await start_server(connector, args)


async def start_configuration_server_wrapper(connector, args):
    await start_configuration_server(connector, args)


def start(connector: Connector):
    parser = argparse.ArgumentParser(description='Connector CLI')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Setting up 'serve' command
    serve_parser = subparsers.add_parser('serve', help='Start the server')
    _add_serve_command_arguments(serve_parser)
    serve_parser.set_defaults(func=start_server_wrapper)

    # Setting up 'configuration' command
    config_parser = subparsers.add_parser('configuration', help='Configuration server commands')
    config_subparsers = config_parser.add_subparsers(dest='config_command', required=True)

    # Setting up 'configuration serve' command
    config_serve_parser = config_subparsers.add_parser('serve', help='Start the configuration server')
    _add_configuration_serve_command_arguments(config_serve_parser)
    config_serve_parser.set_defaults(func=start_configuration_server_wrapper)

    args = parser.parse_args()
    asyncio.run(args.func(connector, args))


def _add_serve_command_arguments(parser):
    parser.add_argument('--configuration', required=True, help='Path to the configuration file')
    parser.add_argument('--port', type=int, default=8100, help='Port number')
    parser.add_argument('--service-token-secret', help='Service token secret')


def _add_configuration_serve_command_arguments(parser):
    parser.add_argument('--port', type=int, default=9100, help='Port number for configuration server')
    # Add other options as in the Node.js code
