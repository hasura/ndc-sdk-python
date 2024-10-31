from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCTraceExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GRPCMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPTraceExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HTTPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3Format
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.propagate import get_global_textmap
from enum import Enum
import asyncio
import os

sdk = None

USER_VISIBLE_SPAN_ATTRIBUTE = {
    "internal.visibility": "user",
}


class Protocol(str, Enum):
    GRPC = "grpc"
    HTTP_PROTOBUF = "http/protobuf"


def get_exporters(protocol: Protocol, endpoint: str):
    """Get the appropriate exporters based on the protocol."""
    if protocol == Protocol.GRPC:
        trace_exporter = GRPCTraceExporter(endpoint=endpoint)
        metric_exporter = GRPCMetricExporter(endpoint=endpoint)
    elif protocol == Protocol.HTTP_PROTOBUF:
        # For HTTP/protobuf, we need to append the specific endpoints
        trace_endpoint = f"{endpoint}/v1/traces"
        metric_endpoint = f"{endpoint}/v1/metrics"
        trace_exporter = HTTPTraceExporter(endpoint=trace_endpoint)
        metric_exporter = HTTPMetricExporter(endpoint=metric_endpoint)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")

    return trace_exporter, metric_exporter


def init_telemetry(default_service_name="hasura-ndc",
                   default_endpoint="http://localhost:4317",
                   default_protocol="grpc"):
    global sdk

    if is_initialized():
        raise Exception("Telemetry has already been initialized!")

    service_name = os.environ.get("OTEL_SERVICE_NAME", default_service_name)
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", default_endpoint)
    protocol = Protocol(os.environ.get("OTEL_EXPORTER_OTLP_PROTOCOL", default_protocol))

    resource = Resource.create(attributes={"service.name": service_name})

    trace_exporter, metric_exporter = get_exporters(protocol, endpoint)

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    span_processor = BatchSpanProcessor(trace_exporter)
    tracer_provider.add_span_processor(span_processor)

    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    metric_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(metric_provider)

    FastAPIInstrumentor().instrument(
        server_request_hook=lambda span, request: span.set_attributes(USER_VISIBLE_SPAN_ATTRIBUTE)
    )
    RequestsInstrumentor().instrument(
        tracer_provider=trace.get_tracer_provider(),
        span_callback=lambda span, request, response: span.set_attributes(USER_VISIBLE_SPAN_ATTRIBUTE),
    )
    LoggingInstrumentor().instrument(
        log_hook=lambda span, record, _: record.update(
            {
                "resource.service.name": service_name,
                "parent_span_id": span.get_span_context().span_id,
            }
        )
    )

    propagators = CompositePropagator(
        [
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
            B3Format(),
        ]
    )
    set_global_textmap(propagators)

    sdk = trace.get_tracer_provider()


def is_initialized():
    return sdk is not None


async def with_active_span(tracer, name, func, attributes=None, headers: dict = None):
    if headers is None:
        headers = {}
    if attributes is None:
        attributes = {}

    attributes = {**USER_VISIBLE_SPAN_ATTRIBUTE, **attributes}

    # Extract the trace context from the headers
    ctx = get_global_textmap().extract(headers)

    # Get the current span context
    current_span = trace.get_current_span()
    if current_span.is_recording():
        ctx = trace.set_span_in_context(current_span, ctx)

    def handle_error(span, err):
        if isinstance(err, Exception) or isinstance(err, str):
            span.record_exception(err)
        span.set_status(Status(StatusCode.ERROR))

    # Start a new span, passing the extracted context
    with tracer.start_as_current_span(name, attributes=attributes, context=ctx) as span:
        try:
            retval = func(span)
            if asyncio.iscoroutine(retval):
                retval = await retval
            return retval
        except Exception as e:
            handle_error(span, e)
            raise
        finally:
            span.end()
