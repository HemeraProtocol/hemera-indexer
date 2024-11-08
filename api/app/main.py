#!/usr/bin/python3
# -*- coding: utf-8 -*-
import flask
from flask import Flask, request
from flask_cors import CORS

# from app.serializing import ma
from flask_swagger_ui import get_swaggerui_blueprint

from api.app.cache import cache, redis_db
from api.app.limiter import limiter
from common.models import db
from common.utils.config import get_config
from common.utils.exception_control import APIError

config = get_config()

import logging
import os

from flask import Flask, send_file

# logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)


app = Flask(__name__)
# Get the log level from the environment variable, default to WARNING if not set
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

SWAGGER_URL = "/api/docs"
API_YAML_PATH = "/api/swagger.yaml"
YAML_FILE_PATH = "/app/migrations/swagger.yaml"


@app.route("/api/swagger.yaml")
def serve_swagger_yaml():
    return send_file(YAML_FILE_PATH)


swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_YAML_PATH, config={"app_name": "Hemera Protocol API"})

app.register_blueprint(swaggerui_blueprint)


# Convert the string log level to the corresponding numeric value
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
    raise ValueError("Invalid log level: %s" % log_level)

app.logger.setLevel(numeric_level)
# Init database
app.config["SQLALCHEMY_DATABASE_URI"] = config.db_read_sql_alchemy_database_config.get_sql_alchemy_uri()
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
from api.app.api import api

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
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_prelight_response()


@app.after_request
def inject_identifying_headers(response):
    if flask.session.get("user_id"):
        response.headers["X-User-Id"] = flask.session.get("user_id")
    return response
