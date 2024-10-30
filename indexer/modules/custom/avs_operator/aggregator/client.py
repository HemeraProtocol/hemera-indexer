import base64

import requests

from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.modules.custom.avs_operator.aggregator.task import AlertTaskInfo


class AggregatorClient:
    def __init__(self, host):
        self.host = host

    def create_alert_task(self, alert_hash):
        res = requests.post(
            self.host, json={"jsonrpc": "2.0", "method": "aggregator_createTask", "params": [alert_hash], "id": 1}
        )
        if res.status_code != 200:
            raise ValueError(f"Failed to create alert task: {res.text}")

        response_json = res.json()
        if "error" in response_json:
            raise ValueError(f"Failed to create alert task: {response_json['error']}")
        result = response_json["result"]
        alert_task_info = AlertTaskInfo(
            alert_hash=hex_str_to_bytes(result["alert_hash"]),
            quorum_numbers=list(base64.b64decode(result["quorum_numbers"])),
            quorum_threshold_percentages=list(base64.b64decode(result["quorum_threshold_percentages"])),
            task_index=result["task_index"],
            reference_block_number=result["reference_block_number"],
        )
        return alert_task_info

    def send_signed_task_response(self, alert, bls_sign, operator_id):
        alert_data_req = {
            "alert_hash": bytes_to_hex_str(alert.alert_hash),
            "quorum_numbers": alert.quorum_numbers,
            "quorum_threshold_percentages": alert.quorum_threshold_percentages,
            "task_index": alert.task_index,
            "reference_block_number": alert.reference_block_number,
        }
        res = requests.post(
            self.host,
            json={
                "jsonrpc": "2.0",
                "method": "aggregator_processSignedTaskResponse",
                "params": [alert_data_req, bls_sign, operator_id],
                "id": 1,
            },
        )
        if res.status_code != 200:
            raise ValueError(f"Failed to send signed task response: {res.text}")
        if "error" in res.json():
            raise ValueError(f"Failed to send signed task response: {res.json()['error']}")

        return True
