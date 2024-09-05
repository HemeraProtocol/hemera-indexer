import time

from sqlalchemy import text


class InitializationJob:
    def __init__(self, **kwargs):
        config = kwargs["config"]
        self.db_service = config["db_service"]
        self.dblink_url = config["dblink_url"]

    def init_token_price(self):
        token_price_sql_template = """
        CREATE EXTENSION if not exists dblink;

        DELETE FROM token_price WHERE timestamp >= :start_date;

        INSERT INTO token_price
        SELECT * FROM dblink(:dblink_url,
                             'SELECT * FROM w3w_commons.token_hourly_prices WHERE timestamp >= ''{start_date}'' ')
        AS t(symbol varchar, timestamp timestamp, price numeric);
        """

        sql = token_price_sql_template.format(start_date=self.start_date)

        session = self.db_service.Session()

        start_time = time.time()

        session.execute(text(sql), {'start_date': self.start_date, 'dblink_url': self.dblink_url})

        session.commit()
        execution_time = time.time() - start_time
        print(f'----------- executed in {execution_time:.2f} seconds: init token price')

        session.close()

    def init_period_address_token_balance(self):
        session = self.db_service.Session()

        sql_template = """
        delete from period_address_token_balances where period_date >= :start_date;        
        """
        start_time = time.time()
        session.execute(text(sql_template), {'start_date': self.start_date})

        session.commit()
        execution_time = time.time() - start_time
        print(f'----------- executed in {execution_time:.2f} seconds: init token price')

        session.close()

    def run(self, **kwargs):
        self.start_date = kwargs["start_date"]
        self.end_date = kwargs["end_date"]

        self.init_token_price()
        self.init_period_address_token_balance()
