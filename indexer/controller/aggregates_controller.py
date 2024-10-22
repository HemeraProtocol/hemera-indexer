from datetime import datetime, timedelta

from indexer.controller.base_controller import BaseController


class AggregatesController(BaseController):
    def __init__(self, job_dispatcher):
        self.job_dispatcher = job_dispatcher

    def action(self, start_date, end_date, date_batch_size=None):
        # no batch size
        self.job_dispatcher.run(start_date, end_date)

        # batch size
        # date_batches = self.split_date_range(start_date, end_date, date_batch_size)
        # for date_batch in date_batches:
        #     start_date, end_date = date_batch
        #     self.job_dispatcher.run(start_date, end_date)

    @staticmethod
    def split_date_range(start_date, end_date, batch_size):
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        date_ranges = []
        while start_date_obj < end_date_obj:
            batch_end_date = min(start_date_obj + timedelta(days=batch_size - 1), end_date_obj)
            date_ranges.append((start_date_obj.strftime("%Y-%m-%d"), batch_end_date.strftime("%Y-%m-%d")))
            start_date_obj = batch_end_date + timedelta(days=1)

        return date_ranges
