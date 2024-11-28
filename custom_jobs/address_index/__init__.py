from functools import wraps

from flask_restx.namespace import Namespace

address_profile_namespace = Namespace(
    "Address Profile",
    path="/",
    description="Address profile API",
)
