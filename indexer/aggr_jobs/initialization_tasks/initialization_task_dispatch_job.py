import time

from sqlalchemy import text


class InitializationTaskDispatchJob:
    def __init__(self, **kwargs):
        config = kwargs["config"]
        job_list = kwargs["job_list"]
        self.job_list = job_list.get_initialization_jobs()
        self.db_service = config["db_service"]

    def init_period_address_token_balance(self):
        session = self.db_service.Session()

        sql_template = """
        delete from period_address_token_balances where period_date >= :start_date;
        """
        start_time = time.time()
        session.execute(text(sql_template), {"start_date": self.start_date})

        session.commit()
        execution_time = time.time() - start_time
        print(f"----------- executed in {execution_time:.2f} seconds: init period_address_token_balances")

        session.close()

    def run(self, **kwargs):
        self.start_date = kwargs["start_date"]
        self.end_date = kwargs["end_date"]

        for function_name in self.job_list:
            func = getattr(self, function_name, None)
            if callable(func):
                func()
            else:
                print(f"Function {function_name} does not exist")
