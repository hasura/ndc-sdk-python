from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
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
import asyncio
import os

sdk = None

USER_VISIBLE_SPAN_ATTRIBUTE = {
    "internal.visibility": "user",
}


def init_telemetry(default_service_name="hasura-ndc", default_endpoint="http://localhost:4317"):
    global sdk

    if is_initialized():
        raise Exception("Telemetry has already been initialized!")

    service_name = os.environ.get("OTEL_SERVICE_NAME", default_service_name)
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", default_endpoint)

    resource = Resource.create(attributes={"service.name": service_name})

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=endpoint)
    )
    tracer_provider.add_span_processor(span_processor)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint)
    )
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
