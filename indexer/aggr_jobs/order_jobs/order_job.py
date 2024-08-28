from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob

job_list = ['period_address_token_balances', 'period_feature_holding_balance_uniswap_v3.sql', 'period_feature_holding_balance_staked_fbtc_detail.sql']


class AggrOrderJob(AggrBaseJob):
    sql_folder = "order_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        self.db_service = config["db_service"]

    def run(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]

        session = self.db_service.Session()

        date_pairs = self.generate_date_pairs(start_date, end_date)
        for date_pair in date_pairs:
            start_date, end_date = date_pair
            for sql_name in job_list:
                sql_content = self.get_sql_content(sql_name, start_date, end_date)
                session.execute(text(sql_content))
                session.commit()
