#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 17:12
# @Author  will
# @File  __init__.py.py
# @Brief

from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

from hemera.common.enumeration.entity_type import DynamicEntityTypeRegistry
from hemera_udf.eigen_layer.domains import *

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-xxx:{__version__}` needs Hemera 1.0.0+")


value = DynamicEntityTypeRegistry.register("EIGEN_LAYER")
DynamicEntityTypeRegistry.register_output_types(value, {EigenLayerAction, EigenLayerAddressCurrent})
