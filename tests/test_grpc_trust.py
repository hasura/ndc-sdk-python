import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import certifi
import ndc_sdk_python.instrumentation as instrumentation


class GrpcTrustTests(unittest.TestCase):
    def test_default_credentials_use_certifi_for_both_signals(self):
        for signal in ("TRACES", "METRICS"):
            with self.subTest(signal=signal), patch.dict(os.environ, {}, clear=True):
                with patch.object(instrumentation, "ssl_channel_credentials") as credentials:
                    instrumentation._grpc_credentials(signal, "https://collector:4317")
                    credentials.assert_called_once_with(
                        root_certificates=Path(certifi.where()).read_bytes(),
                        private_key=None,
                        certificate_chain=None,
                    )

    def test_exporters_receive_their_signal_credentials(self):
        with patch.object(instrumentation, "_grpc_credentials", side_effect=["traces", "metrics"]) as credentials:
            with patch.object(instrumentation, "GRPCTraceExporter") as traces:
                with patch.object(instrumentation, "GRPCMetricExporter") as metrics:
                    instrumentation.get_exporters(instrumentation.Protocol.GRPC, "https://collector")
                    self.assertEqual(credentials.call_args_list, [
                        unittest.mock.call("TRACES", "https://collector"),
                        unittest.mock.call("METRICS", "https://collector"),
                    ])
                    traces.assert_called_once_with(endpoint="https://collector", credentials="traces")
                    metrics.assert_called_once_with(endpoint="https://collector", credentials="metrics")

    def test_custom_trust_remains_with_exporter(self):
        for variable in (
            "OTEL_EXPORTER_OTLP_CERTIFICATE",
            "OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE",
            "GRPC_DEFAULT_SSL_ROOTS_FILE_PATH",
            "OTEL_PYTHON_EXPORTER_OTLP_GRPC_CREDENTIAL_PROVIDER",
            "OTEL_PYTHON_EXPORTER_OTLP_GRPC_TRACES_CREDENTIAL_PROVIDER",
        ):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: "custom"}, clear=True):
                with patch.object(instrumentation, "ssl_channel_credentials") as credentials:
                    self.assertIsNone(instrumentation._grpc_credentials("TRACES", "https://collector"))
                    credentials.assert_not_called()

    def test_signal_custom_ca_does_not_override_other_signal(self):
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE": "custom"}, clear=True):
            with patch.object(instrumentation, "ssl_channel_credentials") as credentials:
                instrumentation._grpc_credentials("METRICS", "https://collector")
                credentials.assert_called_once()

    def test_insecure_endpoints_do_not_load_credentials(self):
        cases = [
            ("http://collector", {}),
            ("collector:4317", {"OTEL_EXPORTER_OTLP_INSECURE": "true"}),
            ("https://collector", {"OTEL_EXPORTER_OTLP_TRACES_INSECURE": "true"}),
        ]
        # HTTPS wins over insecure=true in the exporter.
        for endpoint, env in cases[:2]:
            with self.subTest(endpoint=endpoint), patch.dict(os.environ, env, clear=True):
                with patch.object(instrumentation, "ssl_channel_credentials") as credentials:
                    self.assertIsNone(instrumentation._grpc_credentials("TRACES", endpoint))
                    credentials.assert_not_called()
        with patch.dict(os.environ, cases[2][1], clear=True):
            with patch.object(instrumentation, "ssl_channel_credentials") as credentials:
                instrumentation._grpc_credentials("TRACES", "https://collector")
                credentials.assert_called_once()

    def test_signal_insecure_overrides_generic_setting(self):
        with patch.dict(os.environ, {
            "OTEL_EXPORTER_OTLP_INSECURE": "true",
            "OTEL_EXPORTER_OTLP_TRACES_INSECURE": "false",
        }, clear=True):
            with patch.object(instrumentation, "ssl_channel_credentials") as credentials:
                instrumentation._grpc_credentials("TRACES", "http://collector")
                credentials.assert_called_once()

    def test_mtls_uses_signal_files_before_generic_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("signal-key", "signal-cert", "generic-key", "generic-cert"):
                (root / name).write_bytes(name.encode())
            env = {
                "OTEL_EXPORTER_OTLP_CLIENT_KEY": str(root / "generic-key"),
                "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE": str(root / "generic-cert"),
                "OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY": str(root / "signal-key"),
                "OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE": str(root / "signal-cert"),
            }
            with patch.dict(os.environ, env, clear=True):
                with patch.object(instrumentation, "ssl_channel_credentials") as credentials:
                    instrumentation._grpc_credentials("TRACES", "https://collector")
                    self.assertEqual(credentials.call_args.kwargs["private_key"], b"signal-key")
                    self.assertEqual(credentials.call_args.kwargs["certificate_chain"], b"signal-cert")
                    instrumentation._grpc_credentials("METRICS", "https://collector")
                    self.assertEqual(credentials.call_args.kwargs["private_key"], b"generic-key")
                    self.assertEqual(credentials.call_args.kwargs["certificate_chain"], b"generic-cert")

    def test_missing_mtls_file_fails_closed(self):
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_CLIENT_KEY": "/nonexistent/key"}, clear=True):
            with self.assertRaises(FileNotFoundError):
                instrumentation._grpc_credentials("TRACES", "https://collector")


if __name__ == "__main__":
    unittest.main()