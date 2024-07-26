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
        # 'base58',
        'requests',
        "sqlalchemy==2.0.31",
        "psycopg2-binary==2.9.9",
        "alembic",
        "pandas",
        'Flask==3.0.3',
        'Flask-Caching==2.0.1',
        'Flask-Cors==3.0.9',
        'flask-limiter==3.8.0',
        'flask-restx==1.3.0',
        'Flask-SQLAlchemy==3.1.1',
        'blinker>=1.8.2',
        'Werkzeug==3.0.3',
        'openpyxl==3.1.3',
        # 'protobuf==4.21.6',
        # 'pycryptodome==3.17',
        # # 'bcrypt==4.0.1',
        'redis==4.5.4',
        'urllib3==2.2.2',
        # 'pytz~=2023.3',
        # 'PyJWT==2.7.0',
        # 'gunicorn==21.2.0',
        # # 'chardet==5.2.0',
        # 'hexbytes==0.3.1',
        'dataclass-wizard==0.22.3',
        "pytest"
        # 'Flask==2.1.3',
        # 'flask-limiter==2.6.3',
        # 'flask-restx==0.5.1',
        # 'Flask-SQLAlchemy==2.5.1',
        # 'Werkzeug==2.0.1',
        # 'openpyxl==3.0.7',
    ],
    extras_require={
        'streaming': [
            'grpcio==1.46.3'
        ],
        'dev': [
            'pytest~=4.3.0'
        ],
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
