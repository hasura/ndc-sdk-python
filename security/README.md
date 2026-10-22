# TLS trust requirements

The published package requires certifi >=2026.10.19, including when installed
as a dependency rather than from this repository's uv.lock. The targeted lock
update fixes the requests-based OTLP HTTP exporter trust bundle.

Use uv >=0.13.4 and pip >=26.2.2 for dependency installation/builds; those tools
have independent trust inputs. The setup-uv actions in this repository do not
pin an older uv version and resolve the latest release by default.

CPython's ssl/urllib, gRPC, native clients, and custom requests CA configuration
can use other trust sources. Update the deployment's OS/runtime trust separately.
This certifi requirement is not a blanket fix for every Python TLS client.

Incident and patched-version reference: https://emudhra.we-have-a-problem.com/

Release validation must show certificate-verification rejection of all 12
published TLS chains (including cross-signs), plus acceptance of an unrelated
valid chain. Timeouts and connection failures are not evidence of distrust.
Rebuild consumers and update immutable deployed image references; an SDK source
change does not modify existing binaries, images, or hibernated instances.
Custom truststores, CA overrides, or custom verification require separate review.
