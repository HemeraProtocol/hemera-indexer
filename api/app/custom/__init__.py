#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask_restx.namespace import Namespace

custom_namespace = Namespace("Custom Explorer", path="/", description="Custom Feature Explorer API")
