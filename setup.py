from setuptools import setup, find_packages

# Read the contents of your README file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='hasura_ndc',
    version='0.07',
    packages=find_packages(),
    install_requires=[
        # This line reads the requirements from your `requirements.txt`
        line.strip() for line in open('requirements.txt', 'r').readlines()
    ],
    author='Tristen Harr',
    author_email='tristen.harr@hasura.io',
    description='A Hasura Data Connector SDK',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    license='Apache License 2.0'
)
