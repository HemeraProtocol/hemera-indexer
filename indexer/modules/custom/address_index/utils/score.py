from datetime import datetime, timezone

from dateutil import parser


def calculate_aci_score(profile, assets, volumes):
    score = 0

    # 1. Transaction activity score (0-40 points)
    tx_count = profile.get("transaction_count", 0)
    if tx_count > 1000:
        score += 40
    elif tx_count > 100:
        score += 30
    elif tx_count > 10:
        score += 20
    elif tx_count > 0:
        score += 10

    # 2. Asset value score (0-30 points)
    total_asset_value_usd = float(assets.get("total_asset_value_usd", "0"))
    if total_asset_value_usd > 1000000:  # $1M+
        score += 30
    elif total_asset_value_usd > 100000:  # $100k+
        score += 20
    elif total_asset_value_usd > 10000:  # $10k+
        score += 10
    elif total_asset_value_usd > 0:
        score += 5

    # 3. Volume score (0-20 points)
    tx_volume = float(volumes.get("transaction_volume", "0"))
    if tx_volume > 1000000:  # $1M+
        score += 20
    elif tx_volume > 100000:  # $100k+
        score += 15
    elif tx_volume > 10000:  # $10k+
        score += 10
    elif tx_volume > 0:
        score += 5

    # 4. Account age score (0-10 points)
    first_tx_time = profile.get("first_block_timestamp")
    if first_tx_time:
        try:
            # Parse the string to datetime if it's a string
            if isinstance(first_tx_time, str):
                first_tx_time = parser.parse(first_tx_time)

            # Ensure first_tx_time is timezone-aware
            if first_tx_time.tzinfo is None:
                first_tx_time = first_tx_time.replace(tzinfo=timezone.utc)

            # Use UTC time for consistency
            current_time = datetime.now(timezone.utc)

            # Calculate the difference in days
            account_age = (current_time - first_tx_time).days

            if account_age > 365 * 2:  # 2+ years
                score += 10
            elif account_age > 365:  # 1+ year
                score += 7
            elif account_age > 180:  # 6+ months
                score += 5
            elif account_age > 30:  # 1+ month
                score += 3
            else:
                score += 1
        except (ValueError, AttributeError) as e:
            # Log the error and continue without adding to the score
            print(f"Error processing first_block_timestamp: {e}")
            # Optionally, you might want to add a minimal score or handle this case differently
            score += 1

    return min(score, 100)
