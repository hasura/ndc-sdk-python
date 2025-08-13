# ndc-sdk-python 

A Python SDK for creating Hasura Native Data Connectors as per the [NDC spec](https://github.com/hasura/ndc-spec/), using the Python programming language.

To install the library you can use:

`pip3 install ndc-sdk-python`

Included in this SDK is an implementation of a Lambda connector, called a FunctionConnector. If you wanted to simply write Python code you'd likely be more interested in the Python Lambda connector which makes use of this, and you can find that repo here: [hasura/ndc-python-lambda](https://github.com/hasura/ndc-python-lambda)

Developer notes:

This repository uses `uv` to control dependencies. To install dependencies, run `uv sync`.
