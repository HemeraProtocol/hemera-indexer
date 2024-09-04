from flask_restx.namespace import Namespace

contract_namespace = Namespace(
    "Explorer Contract Parser",
    path="/",
    description="Explorer Contract Parser API",
)
