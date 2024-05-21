class BaseJob(object):
    data_buff = {}
    index_keys = []

    def run(self):
        try:
            self._start()
            self._export()
        finally:
            self._end()

        return self.data_buff

    def _start(self):
        self.data_buff = {}
        for key in self.index_keys:
            self.data_buff[key] = []

    def _export(self):
        pass

    def _export_item(self, item):
        item_type = item.get('item', None)
        if item_type is None:
            raise ValueError('type key is not found in item {}'.format(repr(item)))

        self.data_buff[item_type].append(item)

    def _end(self):
        pass
