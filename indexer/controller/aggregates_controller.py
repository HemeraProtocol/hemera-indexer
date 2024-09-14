from datetime import datetime, timedelta

from indexer.controller.base_controller import BaseController


class AggregatesController(BaseController):
    def __init__(self, job_dispatcher):
        self.job_dispatcher = job_dispatcher

    def action(self, start_date, end_date, date_batch_size=None):
        # no batch size
        # self.job_dispatcher.run(start_date, end_date)
        self.job_dispatcher.run_initialization_task_dispatch_job(start_date, end_date)
        # batch size
        date_batches = self.split_date_range(start_date, end_date, date_batch_size)
        for date_batch in date_batches:
            start_date_, end_date_ = date_batch
            self.job_dispatcher.run(start_date_, end_date_)

    @staticmethod
    def split_date_range(start_date, end_date, batch_size):
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        date_ranges = []

        # 按批次切分日期范围，并确保批次间的结束日期和下一个批次的开始日期相同
        while start_date_obj < end_date_obj:
            batch_end_date = min(start_date_obj + timedelta(days=batch_size), end_date_obj)
            date_ranges.append((start_date_obj.strftime("%Y-%m-%d"), batch_end_date.strftime("%Y-%m-%d")))
            start_date_obj = batch_end_date  # 让下一个批次的开始日期与当前批次的结束日期接壤

        return date_ranges
