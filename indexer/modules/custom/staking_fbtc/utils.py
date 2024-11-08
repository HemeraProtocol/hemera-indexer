from sqlalchemy import and_, func

from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import (
    StakedFBTCCurrentStatus,
    TransferredFBTCCurrentStatus,
)
from indexer.modules.custom.staking_fbtc.models.feature_staked_fbtc_detail_records import FeatureStakedFBTCDetailRecords


def get_current_status_generic(db_service, contract_list, block_number, status_class):
    if not db_service:
        return {}
    bytea_address_list = [hex_str_to_bytes(address) for address in contract_list]

    session = db_service.get_service_session()
    try:
        latest_blocks = (
            session.query(
                FeatureStakedFBTCDetailRecords.vault_address,
                FeatureStakedFBTCDetailRecords.wallet_address,
                func.max(FeatureStakedFBTCDetailRecords.block_number).label("max_block_number"),
            )
            .filter(FeatureStakedFBTCDetailRecords.vault_address.in_(bytea_address_list))
            .filter(FeatureStakedFBTCDetailRecords.block_number < block_number)
            .group_by(FeatureStakedFBTCDetailRecords.vault_address, FeatureStakedFBTCDetailRecords.wallet_address)
            .subquery()
        )

        result = (
            session.query(FeatureStakedFBTCDetailRecords)
            .join(
                latest_blocks,
                and_(
                    FeatureStakedFBTCDetailRecords.vault_address == latest_blocks.c.vault_address,
                    FeatureStakedFBTCDetailRecords.wallet_address == latest_blocks.c.wallet_address,
                    FeatureStakedFBTCDetailRecords.block_number == latest_blocks.c.max_block_number,
                ),
            )
            .all()
        )

        current_status_map = {}
        if result is not None:
            for item in result:
                contract_address = bytes_to_hex_str(item.vault_address)
                wallet_address = bytes_to_hex_str(item.wallet_address)

                if contract_address not in current_status_map:
                    current_status_map[contract_address] = {}

                current_status_map[contract_address][wallet_address] = status_class(
                    vault_address=contract_address,
                    protocol_id=item.protocol_id,
                    wallet_address=wallet_address,
                    amount=item.amount,
                    block_number=item.block_number,
                    block_timestamp=item.block_timestamp,
                )

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()

    return current_status_map


# Usage for StakedFBTCCurrentStatus
def get_staked_fbtc_status(db_service, staked_contract_list, block_number):
    return get_current_status_generic(db_service, staked_contract_list, block_number, StakedFBTCCurrentStatus)


# Usage for TransferredFBTCCurrentStatus
def get_transferred_fbtc_status(db_service, transferred_contract_list, block_number):
    return get_current_status_generic(db_service, transferred_contract_list, block_number, TransferredFBTCCurrentStatus)
