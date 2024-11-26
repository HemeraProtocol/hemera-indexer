import os
from datetime import datetime, timedelta


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
        sql = sql_template.format(
            start_date=start_date, end_date=end_date, start_date_previous=self.get_previous(start_date)
        )
        return sql

    @staticmethod
    def get_previous(date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        previous_day = date_obj - timedelta(days=1)
        previous_day_str = previous_day.strftime("%Y-%m-%d")
        return previous_day_str

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

    @staticmethod
    def extract_sqls_in_order(jobs_dict, key, sql_type, existing_sqls):
        """
        从 jobs_dict 中提取指定 key 的 sql_type（daily_sqls 或 period_sqls），按顺序添加到 existing_sqls 并去重。
        """
        if key in jobs_dict:
            sqls_dict = jobs_dict[key].get(sql_type, {})
            for sql_list in sqls_dict.values():
                for sql in sql_list:
                    if sql not in existing_sqls:
                        existing_sqls.append(sql)



