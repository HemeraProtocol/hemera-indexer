class BaseDispatcher(object):
    _db_service = None

    def __init__(self, service=None):
        self._db_service = service

    def run(self, *args, **kwargs):
        pass
