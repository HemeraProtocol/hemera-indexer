class BaseController(object):
    db_service = None

    def __init__(self, service):
        self.db_service = service

    def action(self, *args, **kwargs):
        pass

    def shutdown(self):
        pass
