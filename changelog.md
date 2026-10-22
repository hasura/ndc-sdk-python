# Changelog

## [Unreleased]

### Added

### Changed 

### Fixed

## [v0.42.1]

### Fixed

- Require certifi 2026.10.19+ for the requests/OTLP HTTPS trust bundle.
- Use certifi roots for default OTLP/gRPC TLS, which otherwise uses grpcio's separate bundled roots; preserve custom CA configuration and insecure endpoints.

## [v0.42]

- Make field `arguments` non-nullable in schema

## [v0.41]

### Fixed

- Fixes empty capabilities for `exists` and `nested_fields`

## [v0.40]

- Internal project changes to use `uv`

## [v0.39]

### Fixed

- Correctly output empty leaf capabilities for `exists` and `nested_fields`.

<!-- end -->

[Unreleased]: https://github.com/hasura/ndc-sdk-python/compare/v0.42.1...HEAD
[v0.42.1]: https://github.com/hasura/ndc-sdk-python/releases/tag/v0.42.1
[v0.42]: https://github.com/hasura/ndc-sdk-kotlin/releases/tag/v0.42
[v0.41]: https://github.com/hasura/ndc-sdk-kotlin/releases/tag/v0.41
[v0.40]: https://github.com/hasura/ndc-sdk-kotlin/releases/tag/v0.40
[v0.39]: https://github.com/hasura/ndc-sdk-kotlin/releases/tag/v0.39
[v0.38]: https://github.com/hasura/ndc-sdk-kotlin/releases/tag/v0.38
