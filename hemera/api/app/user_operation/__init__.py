#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_restx.namespace import Namespace

user_operation_namespace = Namespace("User Operation Namespace", path="/", description="User Operation API")
