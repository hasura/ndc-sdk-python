# Hasura Python SDK

To install the library you can use:

`pip3 install hasura-ndc`

Python developers can use this SDK to create Hasura Data Connectors using the Python programming language.

You would be interested in this repository if you wanted to write your own Hasura data connector in Python that wrapped a database or custom data-source.

Included in this SDK is an implementation of a Lambda connector, called a FunctionConnector. If you wanted to simply write Python code you'd likely be more interested in the Python Lambda connector which makes use of this, and you can find that repo here: https://github.com/hasura/ndc-python-lambda

Developer notes:

To upload a new version of the Hasura SDK to pypi:

python3 setup.py sdist

python3 setup.py bdist_wheel

twine upload dist/*
