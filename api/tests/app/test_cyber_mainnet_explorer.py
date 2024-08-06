import pytest


@pytest.mark.explorer_api
def test_stats(test_client):
    response = test_client.get("/v1/explorer/stats")
    response_json = response.json

    assert response.status_code == 200
    assert response_json["total_transactions"] > 0
    assert "transaction_tps" in response_json
    assert "latest_batch" in response_json
    assert "latest_block" in response_json
    assert "avg_block_time" in response_json
    assert "eth_price" in response_json
    assert "eth_price_btc" in response_json
    assert "eth_price_diff" in response_json
    assert "native_token_price" in response_json
    assert "native_token_price_eth" in response_json
    assert "native_token_price_diff" in response_json
    assert "dashboard_token_price_eth" in response_json
    assert "dashboard_token_price" in response_json
    assert "dashboard_token_price_diff" in response_json
    assert "gas_fee" in response_json


@pytest.mark.explorer_api
def test_transactions_per_day(test_client):
    response = test_client.get("/v1/explorer/charts/transactions_per_day")
    response_json = response.json

    assert response.status_code == 200
    assert "title" in response_json
    assert response_json["title"] == "Daily Transactions Chart"
    assert "data" in response_json
    assert isinstance(response_json["data"], list)
    assert all("value" in item and "count" in item for item in response_json["data"])


@pytest.mark.explorer_api
def test_explorer_search(test_client):
    q_list = [
        "131",
        "0x319b69888b0d11cec22caa5034e25fffbdc88421",
        "0x9e4ea822b615f8d7f98098a9c7e3950e6acaad2f",
        "0x2D11ae7a83cc5C31093e9F8918E6A905222f536C",
        "0xb3bfa1476895da112550aeb6bb494a25f0fb5302a701fe94433d538211f25619",
        "USDT",
        "0x551f5b690409b9e0482589b1a5b3d32237972f44af8fdb8b6f334c036a943770",
        "godshan.eth",
    ]

    for q in q_list:
        response = test_client.get(f"/v1/explorer/search?q={q}")
        response_json = response.json

        assert response.status_code == 200
        assert isinstance(response_json, list)
        assert all(isinstance(item, dict) and "type" in item for item in response_json)


@pytest.mark.explorer_api
def test_internal_transactions_page1_size10(test_client):
    response = test_client.get("/v1/explorer/internal_transactions?page=1&size=10")
    response_json = response.json

    assert response.status_code == 200
    assert isinstance(response_json, dict)
    assert "data" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "page" in response_json
    assert "size" in response_json

    assert isinstance(response_json["data"], list)
    assert len(response_json["data"]) <= 10
    for transaction in response_json["data"]:
        assert isinstance(transaction, dict)
        assert "from_address" in transaction
        assert "to_address" in transaction
        assert "value" in transaction
        assert "from_address_is_contract" in transaction
        assert "to_address_is_contract" in transaction


@pytest.mark.explorer_api
def test_internal_transactions_page_size_over_10000(test_client):
    response = test_client.get("/v1/explorer/internal_transactions?page=25&size=500")
    assert response.status_code == 400


@pytest.mark.explorer_api
def test_internal_transactions_page_size_either_0(test_client):
    response = test_client.get("/v1/explorer/internal_transactions?page=0&size=20")
    assert response.status_code == 400


@pytest.mark.explorer_api
def test_transactions(test_client):
    response = test_client.get("/v1/explorer/transactions")
    response_json = response.json
    assert response.status_code == 200

    assert response_json["total"] > 0


@pytest.mark.explorer_api
def test_transactions_with_block_num(test_client):
    response = test_client.get("/v1/explorer/transactions?page=10&size=10&block=123")
    response_json = response.json

    assert response.status_code == 200
    assert isinstance(response_json, dict)
    assert "data" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "page" in response_json
    assert "size" in response_json

    assert isinstance(response_json["data"], list)
    assert len(response_json["data"]) <= 10
    for transaction in response_json["data"]:
        assert isinstance(transaction, dict)
        assert "hash" in transaction
        assert "block_number" in transaction
        assert "from_address" in transaction
        assert "to_address" in transaction
        assert "value" in transaction
        assert "block_timestamp" in transaction


@pytest.mark.explorer_api
def test_transactions_with_block_hash(test_client):
    response = test_client.get(
        "/v1/explorer/transactions?page=10&size=10&block=0x41A44E8B108A9EB075FC9297C32D6E0CC6A960DCA7CE8216563D723118E7A953"
    )
    response_json = response.json

    assert response.status_code == 200
    assert isinstance(response_json, dict)
    assert "data" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "page" in response_json
    assert "size" in response_json

    assert isinstance(response_json["data"], list)
    assert len(response_json["data"]) <= 10
    for transaction in response_json["data"]:
        assert isinstance(transaction, dict)
        assert "hash" in transaction
        assert "block_number" in transaction
        assert "from_address" in transaction
        assert "to_address" in transaction
        assert "value" in transaction
        assert "block_timestamp" in transaction


@pytest.mark.explorer_api
def test_transactions_with_address(test_client):
    response = test_client.get(
        "/v1/explorer/transactions?page=10&size=10&address=0xDEADDEADDEADDEADDEADDEADDEADDEADDEAD0001"
    )
    response_json = response.json

    assert response.status_code == 200
    assert isinstance(response_json, dict)
    assert "data" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "page" in response_json
    assert "size" in response_json

    # 检查 data 字段
    assert isinstance(response_json["data"], list)
    assert len(response_json["data"]) <= 10  # 最多返回10条记录
    for transaction in response_json["data"]:
        assert isinstance(transaction, dict)
        assert "hash" in transaction
        assert "block_number" in transaction
        assert "from_address" in transaction
        assert "to_address" in transaction
        assert "value" in transaction
        assert "block_timestamp" in transaction


@pytest.mark.explorer_api
def test_transactions_with_date(test_client):
    response = test_client.get("/v1/explorer/transactions?page=10&size=10&date=20240527")
    response_json = response.json

    assert response.status_code == 200
    assert isinstance(response_json, dict)
    assert "data" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "page" in response_json
    assert "size" in response_json

    # 检查 data 字段
    assert isinstance(response_json["data"], list)
    assert len(response_json["data"]) <= 10  # 最多返回10条记录
    for transaction in response_json["data"]:
        assert isinstance(transaction, dict)
        assert "hash" in transaction
        assert "block_number" in transaction
        assert "from_address" in transaction
        assert "to_address" in transaction
        assert "value" in transaction
        assert "block_timestamp" in transaction


@pytest.mark.explorer_api
def test_explorer_transaction_detail_no_trace(test_client):
    hash = "0xD2F9DF901DD1BC79D9854D8B245597F82C0CD144E4898C3945096E197838FC83"

    response = test_client.get(f"/v1/explorer/transaction/{hash}")
    response_json = response.json

    assert response.status_code == 200

    assert "hash" in response_json
    assert "block_number" in response_json
    assert "from_address" in response_json
    assert "to_address" in response_json


@pytest.mark.explorer_api
def test_explorer_transaction_detail_with_trace(test_client):
    hash = "0xABDA79232D8787FFD190CEC2D2EA3894AD9C899D1D1AAA2937A369717A0D2CFF"

    response = test_client.get(f"/v1/explorer/transaction/{hash}")
    print(response.text)
    response_json = response.json

    assert response.status_code == 200

    assert "hash" in response_json
    assert "block_number" in response_json
    assert "from_address" in response_json
    assert "to_address" in response_json


@pytest.mark.explorer_api
def test_explorer_transaction_logs(test_client):
    hash = "0x42F6C9379551E09E7CCDA661DD0A5C8208A4767803EDA1F8240E47B6B44E48F0"

    response = test_client.get(f"/v1/explorer/transaction/{hash}/logs")
    response_json = response.json

    assert response.status_code == 200

    assert "total" in response_json
    assert "data" in response_json

    assert response_json["total"] >= 0


@pytest.mark.explorer_api
def test_explorer_transaction_token_transfers(test_client):
    hash = "0xDD279FF5C07C5AC723AED96BC34C797A79044A2D6D3539758F975BF499EBC530"

    response = test_client.get(f"/v1/explorer/transaction/{hash}/token_transfers")
    response_json = response.json

    assert response.status_code == 200

    assert "total" in response_json
    assert "data" in response_json

    assert response_json["total"] >= 0


@pytest.mark.explorer_api
def test_explorer_transaction_internal_transactions(test_client):
    hash = "0x3C3EA0E4082D4C1DD98AD9216AF9283A91173B1C5086BBB7CDF790B74CD71D2F"

    response = test_client.get(f"/v1/explorer/transaction/{hash}/internal_transactions")
    response_json = response.json

    assert response.status_code == 200
    assert "total" in response_json
    assert "data" in response_json
    assert response_json["total"] >= 0


@pytest.mark.explorer_api
def test_explorer_transaction_traces(test_client):
    hash = "0x3C3EA0E4082D4C1DD98AD9216AF9283A91173B1C5086BBB7CDF790B74CD71D2F"

    response = test_client.get(f"/v1/explorer/transaction/{hash}/traces")
    response_json = response.json

    assert response.status_code == 200
    assert "data" in response_json
    assert response_json["data"]


@pytest.mark.explorer_api
def test_explorer_tokens_erc20(test_client):
    response = test_client.get("/v1/explorer/tokens?type=erc20&is_verified=False")
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "data" in response_json
    assert response_json["data"] is not None


@pytest.mark.explorer_api
def test_explorer_tokens_erc721(test_client):
    response = test_client.get("/v1/explorer/tokens?type=erc721&is_verified=False")
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "data" in response_json
    assert response_json["data"] is not None


@pytest.mark.explorer_api
def test_explorer_tokens_erc1155(test_client):
    response = test_client.get("/v1/explorer/tokens?type=erc1155&is_verified=False")
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "data" in response_json
    assert response_json["data"] is not None


@pytest.mark.explorer_api
def test_explorer_tokens_transfers(test_client):
    response = test_client.get("/v1/explorer/token_transfers?type=tokentxns")
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "data" in response_json
    assert response_json["data"]


@pytest.mark.explorer_api
def test_explorer_tokens_transfers_token_erc20(test_client):
    response = test_client.get(
        "/v1/explorer/token_transfers?type=tokentxns&token_address=0x6F6238C8EAEA56F54DF418823585D61FDD7DE5DA"
    )
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "data" in response_json
    assert response_json["data"] is not None


@pytest.mark.explorer_api
def test_explorer_tokens_transfers_token_erc721(test_client):
    response = test_client.get(
        "/v1/explorer/token_transfers?type=tokentxns-nft&token_address=0x2473E8D725F7B3ECA344C272F110948D63280F96"
    )
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "data" in response_json
    assert response_json["data"]


@pytest.mark.explorer_api
def test_explorer_tokens_transfers_token_erc1155(test_client):
    response = test_client.get(
        "/v1/explorer/token_transfers?type=tokentxns-nft1155&token_address=0x2E421EB05FFA719C42C280EC0D52B38BB9E7923C"
    )
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "data" in response_json
    assert response_json["data"]


@pytest.mark.explorer_api
def test_explorer_tokens_transfers_address_erc20(test_client):
    response = test_client.get(
        "/v1/explorer/token_transfers?type=tokentxns&address=0xC5A076CAD94176C2996B32D8466BE1CE757FAA27"
    )
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "data" in response_json
    assert response_json["data"]


@pytest.mark.explorer_api
def test_explorer_tokens_transfers_address_erc721(test_client):
    response = test_client.get(
        "/v1/explorer/token_transfers?type=tokentxns-nft&address=0x9CDCBF212CCF4F11BCBC25CCDE18FFCE886F0CA6"
    )
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "data" in response_json
    assert response_json["data"]


@pytest.mark.explorer_api
def test_explorer_tokens_transfers_address_erc1155(test_client):
    response = test_client.get(
        "/v1/explorer/token_transfers?type=tokentxns-nft1155&address=0x9DAB1402AFC2511FCE1C81695DEABD0D79628EBB"
    )
    response_json = response.json

    assert response.status_code == 200
    assert "page" in response_json
    assert "size" in response_json
    assert "total" in response_json
    assert "max_display" in response_json
    assert "data" in response_json
    assert response_json["data"]


@pytest.mark.explorer_api
def test_blocks(test_client):
    response = test_client.get("/v1/explorer/blocks")
    response_json = response.json
    assert response_json["total"] > 0
    assert response.status_code == 200


@pytest.mark.explorer_api
def test_explorer_block_detail_with_number(test_client):
    response = test_client.get("/v1/explorer/block/2024")
    response_json = response.json

    assert response.status_code == 200

    assert "internal_transaction_count" in response_json
    assert "gas_fee_token_price" in response_json
    assert "seconds_since_last_block" in response_json
    assert "is_last_block" in response_json


@pytest.mark.explorer_api
def test_explorer_block_detail_with_hash(test_client):
    response = test_client.get("/v1/explorer/block/0xF4CF31E1084D299C68D5CF9C87F080C90AA3E73B97CC79C296E92F088E1241C7")
    response_json = response.json

    assert response.status_code == 200

    assert "internal_transaction_count" in response_json
    assert "gas_fee_token_price" in response_json
    assert "seconds_since_last_block" in response_json
    assert "is_last_block" in response_json


@pytest.mark.explorer_api
def test_explorer_address_profile(test_client):
    address = "0x65FDF210CC6681A7CC911EC101A6F014F6798BE2"
    response = test_client.get(f"/v1/explorer/address/{address}/profile")
    response_json = response.json

    assert response.status_code == 200

    # 检查基本字段
    assert "balance" in response_json
    assert "native_token_price" in response_json
    assert "balance_dollar" in response_json
    assert "is_contract" in response_json
    assert "is_token" in response_json

    # 检查合同相关字段
    if response_json["is_contract"]:
        assert "contract_creator" in response_json
        assert "transaction_hash" in response_json
        assert "is_verified" in response_json
        assert "is_proxy" in response_json
        assert "implementation_contract" in response_json
        assert "verified_implementation_contract" in response_json

    # 检查令牌相关字段
    if response_json["is_token"]:
        assert "token_type" in response_json
        assert "token_name" in response_json
        assert "token_symbol" in response_json
        assert "token_logo_url" in response_json


@pytest.mark.explorer_api
def test_explorer_address_token_holdings_v1(test_client):
    address = "0xA3DF90BF8E8183A74B537B27E3955BA7D8DE199C"
    response = test_client.get(f"/v1/explorer/address/{address}/token_holdings")
    response_json = response.json

    assert response.status_code == 200

    assert "data" in response_json
    assert "total" in response_json

    token_holder_list = response_json["data"]
    total_count = response_json["total"]

    assert isinstance(token_holder_list, list)
    assert isinstance(total_count, int)

    if token_holder_list:
        sample_token = token_holder_list[0]
        assert "token_address" in sample_token
        assert "balance" in sample_token
        assert "token_id" in sample_token
        assert "token_name" in sample_token
        assert "token_symbol" in sample_token
        assert "token_logo_url" in sample_token
        assert "type" in sample_token

        assert sample_token["type"] in [
            "tokentxns",
            "tokentxns-nft",
            "tokentxns-nft1155",
        ]


@pytest.mark.explorer_api
def test_explorer_address_token_holdings_v2(test_client):
    address = "0xA3DF90BF8E8183A74B537B27E3955BA7D8DE199C"
    response = test_client.get(f"/v2/explorer/address/{address}/token_holdings")
    response_json = response.json

    assert response.status_code == 200

    assert "data" in response_json
    assert "total" in response_json

    token_holder_list = response_json["data"]
    total_count = response_json["total"]

    assert isinstance(token_holder_list, list)
    assert isinstance(total_count, int)

    if token_holder_list:
        sample_token = token_holder_list[0]
        assert "token_address" in sample_token
        assert "balance" in sample_token
        assert "token_id" in sample_token
        assert "token_name" in sample_token
        assert "token_symbol" in sample_token
        assert "token_logo_url" in sample_token
        assert "type" in sample_token

        assert sample_token["type"] in [
            "tokentxns",
            "tokentxns-nft",
            "tokentxns-nft1155",
        ]


@pytest.mark.explorer_api
def test_explorer_address_transactions(test_client):
    address = "0xDEADDEADDEADDEADDEADDEADDEADDEADDEAD0001"
    response = test_client.get(f"/v1/explorer/address/{address}/transactions")
    response_json = response.json

    assert response.status_code == 200

    assert "data" in response_json
    assert "total" in response_json

    transaction_list = response_json["data"]
    total_count = response_json["total"]

    assert isinstance(transaction_list, list)
    assert isinstance(total_count, int)

    if transaction_list:
        sample_transaction = transaction_list[0]
        assert "hash" in sample_transaction
        assert "from_address" in sample_transaction
        assert "to_address" in sample_transaction
        assert "value" in sample_transaction
        assert "block_number" in sample_transaction
        assert "block_timestamp" in sample_transaction


@pytest.mark.explorer_api
def test_explorer_address_token_transfers(test_client):
    paras = [
        {
            "address": "0xA3DF90BF8E8183A74B537B27E3955BA7D8DE199C",
            "transfer_type": "tokentxns",
        },
        {
            "address": "0x9F4BF1FAFD578AE36A96C1E44ED8EC9DAFCF4593",
            "transfer_type": "tokentxns-nft",
        },
        {
            "address": "0xEA792BF7B860C0D074DB81B0BE91F41B1B9C1641",
            "transfer_type": "tokentxns-nft1155",
        },
    ]

    for para in paras:
        address = para["address"]
        transfer_type = para["transfer_type"]

        response = test_client.get(f"/v1/explorer/address/{address}/token_transfers?type={transfer_type}")
        response_json = response.json

        assert response.status_code == 200

        assert "total" in response_json
        assert "data" in response_json
        assert "type" in response_json

        total_count = response_json["total"]
        token_transfer_list = response_json["data"]
        transfer_type_response = response_json["type"]

        assert isinstance(total_count, int)
        assert isinstance(token_transfer_list, list)
        assert isinstance(transfer_type_response, str)

        assert transfer_type_response == transfer_type

        if token_transfer_list:
            sample_transfer = token_transfer_list[0]
            assert "from_address" in sample_transfer
            assert "to_address" in sample_transfer
            assert "token_address" in sample_transfer
            assert "token_name" in sample_transfer
            assert "token_symbol" in sample_transfer
            assert "token_logo_url" in sample_transfer


@pytest.mark.explorer_api
def test_explorer_address_internal_transactions(test_client):
    address = "0x1A8D6D5ABD8948B647C51BB7B071B718FD90D6FF"

    response = test_client.get(f"/v1/explorer/address/{address}/internal_transactions")
    response_json = response.json

    assert response.status_code == 200

    assert "total" in response_json
    assert "data" in response_json

    total_count = response_json["total"]
    transaction_list = response_json["data"]

    assert isinstance(total_count, int)
    assert isinstance(transaction_list, list)

    if transaction_list:
        sample_transaction = transaction_list[0]
        assert "from_address" in sample_transaction
        assert "to_address" in sample_transaction
        assert "value" in sample_transaction
        assert "from_address_is_contract" in sample_transaction
        assert "to_address_is_contract" in sample_transaction
        assert "block_number" in sample_transaction
        assert "transaction_index" in sample_transaction
        assert "value" in sample_transaction

        assert isinstance(sample_transaction["from_address"], str)
        assert isinstance(sample_transaction["to_address"], str)
        assert isinstance(sample_transaction["value"], str)
        assert isinstance(sample_transaction["from_address_is_contract"], bool)
        assert isinstance(sample_transaction["to_address_is_contract"], bool)
        assert isinstance(sample_transaction["block_number"], int)
        assert isinstance(sample_transaction["transaction_index"], int)


@pytest.mark.explorer_api
def test_explorer_address_logs(test_client):
    address = "0x19F4147568D76B8A68B3755589ECD09A6B97ACB7"

    response = test_client.get(f"/v1/explorer/address/{address}/logs")
    response_json = response.json

    assert response.status_code == 200

    assert "total" in response_json
    assert "data" in response_json

    total_count = response_json["total"]
    log_list = response_json["data"]

    assert isinstance(total_count, int)
    assert isinstance(log_list, list)

    if log_list:
        sample_log = log_list[0]
        assert "transaction_hash" in sample_log
        assert "block_number" in sample_log
        assert "log_index" in sample_log
        assert "address" in sample_log
        assert "data" in sample_log
        assert "topic0" in sample_log

        assert isinstance(sample_log["transaction_hash"], str)
        assert isinstance(sample_log["block_number"], int)
        assert isinstance(sample_log["log_index"], int)
        assert isinstance(sample_log["address"], str)
        assert isinstance(sample_log["data"], str)
        assert isinstance(sample_log["topic0"], str)


@pytest.mark.explorer_api
def test_explorer_token_profile(test_client):
    addresses = [
        "0x7A524C7E82874226F0B51AADE60A1BE4D430CF0F",
        "0xEB5FB40B071C0D59449A3E12A09DBD0E23F4836E",
        "0x2E421EB05FFA719C42C280EC0D52B38BB9E7923C",
    ]

    for address in addresses:
        response = test_client.get(f"/v1/explorer/token/{address}/profile")
        response_json = response.json

        assert response.status_code == 200

        assert "token_name" in response_json
        assert "token_checksum_address" in response_json
        assert "token_address" in response_json
        assert "token_symbol" in response_json
        assert "token_logo_url" in response_json
        assert "token_urls" in response_json
        assert "social_medias" in response_json
        assert "token_description" in response_json
        assert "total_supply" in response_json
        assert "total_holders" in response_json
        assert "total_transfers" in response_json
        assert "type" in response_json


@pytest.mark.explorer_api
def test_explorer_token_transfers(test_client):
    addresses = [
        "0x7A524C7E82874226F0B51AADE60A1BE4D430CF0F",
        "0xEB5FB40B071C0D59449A3E12A09DBD0E23F4836E",
        "0x2E421EB05FFA719C42C280EC0D52B38BB9E7923C",
    ]

    for address in addresses:
        response = test_client.get(f"/v1/explorer/token/{address}/token_transfers")
        response_json = response.json

        assert response.status_code == 200

        assert "total" in response_json
        assert "data" in response_json
        assert "type" in response_json

        assert isinstance(response_json["total"], int)
        assert isinstance(response_json["data"], list)
        assert isinstance(response_json["type"], str)


@pytest.mark.explorer_api
def test_explorer_token_top_holders_v2(test_client):
    token_addresses = [
        "0x7A524C7E82874226F0B51AADE60A1BE4D430CF0F",
        "0xEB5FB40B071C0D59449A3E12A09DBD0E23F4836E",
        "0x2E421EB05FFA719C42C280EC0D52B38BB9E7923C",
    ]
    for token_address in token_addresses:
        response = test_client.get(f"/v2/explorer/token/{token_address}/top_holders?page=1&size=10")
        response_json = response.json

        assert response.status_code == 200

        assert "data" in response_json
        assert "total" in response_json

        assert isinstance(response_json["total"], int)
        assert isinstance(response_json["data"], list)

        for holder in response_json["data"]:
            assert "token_address" in holder
            assert "wallet_address" in holder
            assert "balance" in holder
            assert isinstance(holder["token_address"], str)
            assert isinstance(holder["wallet_address"], str)
            assert isinstance(holder["balance"], str)


@pytest.mark.explorer_api
def test_charts(test_client):
    response = test_client.get("/v1/explorer/charts/transactions_per_day")
    assert response.status_code == 200
    response_json = response.json
    assert "data" in response_json
    # assert len(response_json["data"]) == 14


if __name__ == "__main__":
    pytest.main([__file__])
