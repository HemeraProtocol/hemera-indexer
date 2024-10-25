class JobListGenerator(object):
    def __init__(self, job_name):
        self.job_name = job_name

    def get_initialization_jobs(self):
        job_list = []
        if self.job_name == "FBTC":
            job_list = ["init_token_price", "init_period_address_token_balance"]
        return job_list

    def get_disordered_jobs(self):
        job_list = []

        if self.job_name == "FBTC":
            job_list = [
                "daily_feature_holding_balance_staked_fbtc_detail.sql",
                "daily_feature_holding_balance_uniswap_v3.sql",
                "daily_address_token_balances",
                "daily_feature_erc20_token_supply_records.sql",
                # 'daily_feature_erc1155_token_holdings.sql',
                # 'daily_feature_erc1155_token_supply_records.sql'
            ]
        elif self.job_name == "EXPLORE":
            job_list = [
                "test.sql",
                # "daily_explore_aggregates.sql",
            ]

        return job_list

    def get_order_jobs(self):
        job_list = []

        if self.job_name == "FBTC":
            job_list = [
                "period_address_token_balances",
                "period_feature_holding_balance_uniswap_v3.sql",
                "period_feature_staked_fbtc_detail_records.sql",
                "period_feature_holding_balance_staked_fbtc_detail.sql",
                # 'period_feature_erc1155_token_holdings.sql',
                "period_feature_erc1155_token_supply_records.sql",
                "period_feature_holding_balance_merchantmoe.sql",
                "period_feature_erc20_token_supply_records.sql",
                "period_feature_holding_balance_dodo.sql",
                "period_feature_holding_balance_lendle.sql",
                "period_feature_defi_wallet_fbtc_aggregates.py",
            ]
        elif self.job_name == "EXPLORE":
            job_list = [
                "test.sql",
                "explorer_1_update_address_txn_stats.sql",
                "explorer_2_update_address_token_transfer_stats.sql",
                "explorer_3_addresses.sql",
                "explorer_4_agg_address_stats.sql",
                "explorer_5_update_schedule_metadata.sql",
            ]

        return job_list
