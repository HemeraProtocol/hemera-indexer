"""Web Server Gateway Interface"""

##################
# FOR PRODUCTION
# https://www.datascienceblog.net/post/programming/flask-api-development/
####################
from socialscan_api.app.main import app

if __name__ == "__main__":
    ####################
    # FOR DEVELOPMENT
    ####################

    # from app.socialscan import models as w3w_socialscan_models

    # w3w_socialscan_models.postgres_db.create_all(app=app)

    app.run("0.0.0.0", 8082, threaded=True, debug=True)
