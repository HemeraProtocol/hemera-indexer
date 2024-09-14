from datetime import datetime, timedelta

from indexer.controller.base_controller import BaseController


class AggregatesController(BaseController):
    def __init__(self, job_dispatcher):
        self.job_dispatcher = job_dispatcher

    def action(self, start_date, end_date, date_batch_size=None):
        # no batch size
        # self.job_dispatcher.run(start_date, end_date)

        # batch size
        date_batches = self.split_date_range_with_pairs(start_date, end_date, date_batch_size)
        for date_batch in date_batches:
            start_date_, end_date_ = date_batch
            self.job_dispatcher.run(start_date_, end_date_)

    @staticmethod
    def split_date_range_with_pairs(start_date, end_date, batch_size):
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        date_pairs = []

        current_date = start_date_obj
        while current_date < end_date_obj:
            next_date = current_date + timedelta(days=1)
            date_pairs.append((current_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d")))
            current_date = next_date

        batch_ranges = []
        for i in range(0, len(date_pairs), batch_size):
            batch_ranges.append(date_pairs[i:i + batch_size])

        return batch_ranges
