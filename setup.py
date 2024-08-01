import os

from setuptools import find_packages, setup

with open("VERSION", "r") as f:
    version = f.read().strip()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


long_description = read("README.md") if os.path.isfile("README.md") else ""

setup(
    name="hemera-indexer",
    version=version,
    author="xuzh",
    author_email="zihao.xu@thehemera.com",
    description="Tools for exporting Ethereum blockchain data to JSON/CSV file and postgresql",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HemeraProtocol/hemera-indexer",
    packages=find_packages(exclude=["schemas", "tests"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="ethereum",
    python_requires=">=3.8,<4",
    install_requires=[
        "web3>=6.8.0, <7",
        "eth-utils>=4.0.0",
        "eth-abi>=5.0.1",
        "python-dateutil>=2.8.0,<3",
        "click>=8.0.4,<9",
        "ethereum-dasm==0.1.5",
        "requests",
        "sqlalchemy==2.0.31",
        "psycopg2-binary==2.9.9",
        "alembic",
        "pandas",
        "Flask==3.0.3",
        "Flask-Caching==2.3.0",
        "Flask-Cors==3.0.9",
        "flask-limiter==3.8.0",
        "flask-restx==1.3.0",
        "Flask-SQLAlchemy==3.1.1",
        "blinker>=1.8.2",
        "Werkzeug==3.0.3",
        "openpyxl==3.1.3",
        "redis==5.0.7",
        "urllib3==2.2.2",
        "dataclass-wizard==0.22.3",
        "redis-dict",
    ],
    extras_require={
        "streaming": ["grpcio==1.46.3"],
        "dev": [
            "pytest~=4.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hemera=hemera.cli:cli",
        ],
    },
    package_data={
        "hemera": ["*.json", "*.yaml"],
    },
    include_package_data=True,
    license="MIT",
    project_urls={
        "Bug Reports": "https://github.com/HemeraProtocol/hemera-indexer/issues",
        "Chat": "",
        "Source": "https://github.com/HemeraProtocol/hemera-indexer",
    },
)
