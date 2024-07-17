#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

import flask
import sentry_sdk
from flask import Flask, request
from flask_cors import CORS
from sentry_sdk.integrations.flask import FlaskIntegration

from common.models import db
from common.utils.config import get_config
from socialscan_api.app.cache import cache, redis_db
from socialscan_api.app.limiter import get_real_ip, limiter
from common.utils.exception_control import APIError

# from app.serializing import ma

config = get_config()

logging.basicConfig(level=logging.INFO)
# logging.basicConfig()
# logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)

sentry_sdk.init(
    dsn="https://86881b1d137645f094afed7f0ee3c174@o1376794.ingest.sentry.io/4505464387862528",
    integrations=[
        FlaskIntegration(),
    ],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.01,
    # By default the SDK will try to use the SENTRY_RELEASE
    # environment variable, or infer a git commit
    # SHA as release, however you may want to set
    # something more human-readable.
    # release="myapp@1.0.0",
    environment='local',
)

app = Flask(__name__)

# Init database
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_read_sql_alchemy_database_config.get_sql_alchemy_uri()
app.config["SQLALCHEMY_BINDS"] = {
    "common": config.db_common_sql_alchemy_database_config.get_sql_alchemy_uri(),
    "write": config.db_write_sql_alchemy_database_config.get_sql_alchemy_uri(),
}
app.config.update(
    {
        "MAX_CONTENT_LENGTH": 1024 * 1024 * 1024,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_size": 100,
            "max_overflow": 100,
        },
    }
)

db.init_app(app)

# Add API Namespace
from socialscan_api.app.api import api

api.init_app(app)

# Init cache
cache.init_app(app, config.cache_config.get_cache_config(redis_db))

# Rate limit
limiter.init_app(app)

# ma.init_app(app)
CORS(app)
# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See https://flask.palletsprojects.com/quickstart/#sessions.
app.secret_key = "a330c710ea827a698cf64dba73d99080b1bc38aaeedb37967ed840679a6a11c7"


@app.errorhandler(APIError)
def handle_exception(err):
    """Return custom JSON when APIError or its children are raised"""
    app.logger.error(f"New Error: {err.code}: {err.message}")
    return flask.jsonify(err.to_dict()), err.code


@api.errorhandler(APIError)
def handle_exception(err):
    """Return custom JSON when APIError or its children are raised"""
    app.logger.error(f"API Error: {err.code}: {err.message}")
    return err.to_dict(), err.code


# @app.errorhandler(GrpcError)
# def handle_exception(err):
#     """Return custom JSON when Grpc or its children are raised"""
#     app.logger.error(f"Grpc Error: {err.code}: {err.message}")
#     return err.to_dict(), err.code


@app.errorhandler(500)
def handle_exception(err):
    """Return JSON instead of HTML for any other server error"""
    app.logger.error(f"Unknown Exception: {str(err)}")
    response = {
        "code": 500,
        "message": "Sorry, that error is on us, please contact support if this wasn't an accident",
    }
    return flask.jsonify(response), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    response = {"code": 429, "message": f"ratelimit exceeded {e.description}"}
    return flask.jsonify(response), 500


def _build_cors_prelight_response():
    response = flask.make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


@app.before_request
def hook():
    if get_real_ip() in ["182.253.52.70", "37.27.101.162"]:
        raise APIError("Forbidden", 403)

    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_prelight_response()


@app.after_request
def inject_identifying_headers(response):
    if flask.session.get("user_id"):
        response.headers["X-User-Id"] = flask.session.get("user_id")
    return response
