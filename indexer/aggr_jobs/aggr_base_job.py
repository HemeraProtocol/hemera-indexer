import os
from datetime import datetime, timedelta
from sqlalchemy import text

from indexer.executors.batch_work_executor import BatchWorkExecutor


class AggrBaseJob:
    sql_folder = ""

    def run(self, **kwargs):
        pass

    def get_sql_content(self, file_name, start_date, end_date):
        base_dir = os.path.dirname(__file__)
        if not file_name.endswith(".sql"):
            file_name += ".sql"
        file_path = os.path.join(base_dir, self.sql_folder, file_name)

        with open(file_path, "r") as f:
            sql_template = f.read()
        sql = sql_template.format(start_date=start_date, end_date=end_date)
        return sql

    @staticmethod
    def generate_date_pairs(start_date, end_date):
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        date_pairs = []
        current_date = start_date_obj
        while current_date < end_date_obj:
            next_date = current_date + timedelta(days=1)
            if next_date <= end_date_obj:
                date_pairs.append((current_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d")))
            current_date = next_date

        return date_pairs
