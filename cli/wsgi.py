"""Web Server Gateway Interface"""
import click

##################
# FOR PRODUCTION
# https://www.datascienceblog.net/post/programming/flask-api-development/
####################
from api.app.main import app


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
def wsgi():
    ####################
    # FOR DEVELOPMENT
    ####################

    # from app.socialscan import models as w3w_socialscan_models

    # w3w_socialscan_models.postgres_db.create_all(app=app)

    app.run("0.0.0.0", 8082, threaded=True, debug=True)
