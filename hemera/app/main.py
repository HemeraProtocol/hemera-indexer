#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/19 16:24
# @Author  will
# @File  main.py
# @Brief
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from hemera.app.api.routes.developer.es_adapter.router import router as developer_router
from hemera.app.api.routes.explorer.base import router as base_router
from hemera.app.api.routes.explorer.block import router as block_router
from hemera.app.api.routes.explorer.export import router as export_router
from hemera.app.api.routes.explorer.transaction import router as transaction_router
from hemera.app.api.routes.stats import router as stats_router

app = FastAPI(
    title="Hemera Explorer API",
    description="This is my API documentation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.include_router(block_router)
app.include_router(base_router)
app.include_router(transaction_router)
app.include_router(developer_router)
app.include_router(export_router)
app.include_router(stats_router)


def serialize_errors(errors):
    if isinstance(errors, list):
        return [serialize_errors(item) for item in errors]
    elif isinstance(errors, dict):
        new_dict = {}
        for key, value in errors.items():
            new_dict[key] = serialize_errors(value)
        return new_dict
    elif isinstance(errors, ValueError):
        return str(errors)
    else:
        return errors


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    errors_serializable = serialize_errors(exc.errors())
    return JSONResponse(
        status_code=400,
        content={"status": "0", "message": "Invalid input parameters", "result": {"errors": errors_serializable}},
    )
