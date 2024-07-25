import os

from setuptools import find_packages, setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


long_description = read('README.md') if os.path.isfile("README.md") else ""

setup(
    name='hemera-indexer',
    version='0.0.1',
    author='xuzh',
    author_email='zihao.xu@thehemera.com',
    description='Tools for exporting Ethereum blockchain data to JSON/CSV file and postgresql',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/HemeraProtocol/hemera-indexer',
    packages=find_packages(exclude=['schemas', 'tests']),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    keywords='ethereum',
    python_requires='>=3.8,<4',
    install_requires=[
        'web3>=6.8.0, <7',
        "eth-utils>=4.0.0",
        "eth-abi>=5.0.1",
        'python-dateutil>=2.8.0,<3',
        'click>=8.0.4,<9',
        'ethereum-dasm==0.1.5',
        # 'airflow==2.9.1',
        'base58',
        'requests',
        "sqlalchemy",
        "psycopg2-binary==2.9.9",
        "alembic",
        "pandas",
        "numpy==1.26.0",
        'firebase-admin==6.1.0',
        'Flask==2.1.3',
        'Flask-Caching==2.0.1',
        'Flask-Cors==3.0.9',
        'flask-limiter==2.6.3',
        'flask-restx==0.5.1',
        'Flask-SQLAlchemy==2.5.1',
        'sentry-sdk==1.9.5',
        'blinker==1.4',
        'SQLAlchemy==1.4.46',
        'Werkzeug==2.0.1',
        'openpyxl==3.0.7',
        'ShopifyAPI==12.2.0',
        'psycopg2-binary==2.9.9',
        'protobuf==4.21.6',
        'pycryptodome==3.17',
        'boto3==1.26.107',
        'bcrypt==4.0.1',
        'redis==4.5.4',
        'urllib3==1.26.12',
        'pytz~=2023.3',
        'PyJWT==2.7.0',
        'gunicorn==21.2.0',
        'chardet==5.2.0',
        'openai==1.29.0',
        'hexbytes==0.3.1',
        'langchain-core==0.1.52',
        'langchain-openai==0.1.6',
        'dataclass-wizard==0.22.3',
    ],
    extras_require={
        'streaming': [
            # 'timeout-decorator==0.4.1',
            # 'google-cloud-pubsub==2.13.0',
            # 'google-cloud-storage==1.33.0',
            # 'kafka-python==2.0.2',
            'sqlalchemy==1.4',
            # This library is a dependency for google-cloud-pubsub, starting from 0.3.22 it requires Rust,
            # that's why  we lock the version here
            # 'libcst==0.3.21',
            # Later versions break the build in Travis CI for Python 3.7.2
            'grpcio==1.46.3'
        ],
        'streaming-kinesis': [
            'boto3==1.24.11',
            'botocore==1.27.11',
        ],
        'dev': [
            'pytest~=4.3.0'
        ],
        'socialscan-api':
            [
                'firebase-admin==6.1.0',
                'Flask==2.1.3',
                'Flask-Caching==2.0.1',
                'Flask-Cors==3.0.9',
                'flask-limiter==2.6.3',
                'flask-restx==0.5.1',
                'Flask-SQLAlchemy==2.5.1',
                'sentry-sdk==1.9.5',
                'blinker==1.4',
                'SQLAlchemy==1.4.46',
                'Werkzeug==2.0.1',
                'openpyxl==3.0.7',
                'ShopifyAPI==12.2.0',
                'psycopg2-binary==2.9.9',
                'protobuf==4.21.6',
                'pycryptodome==3.17',
                'boto3==1.26.107',
                'bcrypt==4.0.1',
                'redis==4.5.4',
                'urllib3==1.26.12',
                'pytz~=2023.3',
                'PyJWT==2.7.0',
                'gunicorn==21.2.0',
                'chardet==5.2.0',
                'openai==1.29.0',
                'hexbytes==0.3.1',
                'langchain-core==0.1.52',
                'langchain-openai==0.1.6',
                'dataclass-wizard==0.22.3'
            ]
    },
    entry_points={
        'console_scripts': [
            'hemera=hemera.cli:cli',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/HemeraProtocol/hemera-indexer/issues',
        'Chat': '',
        'Source': 'https://github.com/HemeraProtocol/hemera-indexer',
    },
)
