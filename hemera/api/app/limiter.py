#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask import request
from flask_limiter import Limiter


def get_real_ip() -> str:
    remote_address = request.remote_addr
    forward_address = request.headers.get("gateway-forwarded-ip")
    # current_app.logger.info(f"remote_address: {remote_address}")
    # current_app.logger.info(f"gateway-forwarded-ip: {forward_address}")
    # if forward_address:
    #     remote_address = forward_address
    # current_app.logger.info(f"remote_address: {remote_address}")
    return forward_address or remote_address


# https://flask-limiter.readthedocs.io/en/stable/index.html
limiter = Limiter(
    key_func=get_real_ip,
    default_limits=["36000 per hour", "180 per minute"],
    storage_uri="memory://",
)
