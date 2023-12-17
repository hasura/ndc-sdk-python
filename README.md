Hasura Python SDK

pip3 install hasura_ndc

Work in progress

python3 main.py serve --configuration config.json --port 8101 --service-token-secret secret

python3 main.py configuration serve --port 9101


Upload to pypi:

python3 setup.py sdist

python3 setup.py bdist_wheel

twine upload dist/*             
