from flask_restx.namespace import Namespace

address_features_namespace = Namespace(
    "Address Features",
    path="/",
    description="Address Features API",
)
