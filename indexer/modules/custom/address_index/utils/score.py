from datetime import datetime, timezone

from dateutil import parser


def calculate_aci_score(profile, assets, volumes):
    """
    Calculate ACI (Activity Credibility Index) score based on various metrics

    Args:
        profile (dict): Contains transaction_count and first_block_timestamp
        assets (dict): Contains total_asset_value_usd
        volumes (dict): Contains transaction_volume

    Returns:

    """
    base_score = 580

    # 1. TVL/Asset Score (0-100 points)
    asset_value = float(assets.get("total_asset_value_usd", 0))
    if asset_value >= 100000:
        tvl_score = 100.0
    elif asset_value >= 10000:
        tvl_score = ((asset_value - 10000.0) / 90000.0) * 20.0 + 80.0
    elif asset_value >= 100:
        tvl_score = ((asset_value - 100.0) / 9900.0) * 80.0
    else:
        tvl_score = 0.0

    # 2. Transaction Count Score (0-100 points)
    tx_count = profile.get("transaction_count", 0)
    if tx_count >= 10000:
        tx_score = 100.0
    elif tx_count <= 10:
        tx_score = 0.0
    else:
        tx_score = ((tx_count - 10.0) / 9990.0) * 100.0

    # 3. Transaction Volume/Gas Fee Score (0-50 points)
    tx_volume = float(volumes.get("total_gas_fee_used_eth", 0))
    if tx_volume >= 10:
        volume_score = 50.0
    elif tx_volume == 0:
        volume_score = 0.0
    else:
        volume_score = (tx_volume / 10.0) * 50.0

    # 4. Account Age Score (0-70 points)
    first_timestamp = profile.get("first_block_timestamp")
    age_score = 0.0
    if first_timestamp:
        first_time = datetime.fromisoformat(first_timestamp).timestamp()
        current_time = datetime.now().timestamp()
        account_age_months = (current_time - first_time) / (30 * 24 * 60 * 60)  # Convert seconds to months

        if account_age_months >= 120:  # 10 years or more
            age_score = 70.0
        elif account_age_months >= 3:  # Between 3 months and 10 years
            age_score = ((account_age_months - 3) / (120 - 3)) * 70.0

    final_score = base_score + tvl_score + tx_score + volume_score + age_score

    return min(round(final_score, 2), 850)
