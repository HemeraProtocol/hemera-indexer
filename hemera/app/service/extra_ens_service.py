#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/25 14:40
# @Author  ideal93
# @File  extra_ens_service.py.py
# @Brief
import requests


class ExtraEnsService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ExtraEnsService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, service_host="http://ens-service:8080"):
        if self._initialized:
            return
        self.ENS_SERVICE_HOST = service_host
        self.NORMAL_TIMEOUT = 5
        self._initialized = True

    def post_json_response(self, endpoint, payload=None):
        request_url = endpoint
        try:
            response = requests.post(request_url, json=payload, timeout=self.NORMAL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            print(f"Failed to get JSON response: {e}")
            return {}

    def get_json_response(self, endpoint):
        request_url = endpoint
        try:
            response = requests.get(request_url, timeout=self.NORMAL_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            print(f"Failed to get JSON response: {e}")
            return {}

    def get_address_ens(self, address):
        url = f"{self.ENS_SERVICE_HOST}/v1/ens/address/{address}"
        return self.get_json_response(url)

    def get_ens_address(self, ens_name):
        url = f"{self.ENS_SERVICE_HOST}/v1/ens/name/{ens_name}"
        return self.get_json_response(url)

    def batch_get_address_ens(self, address_list):
        url = f"{self.ENS_SERVICE_HOST}/v1/ens/batch/address"
        payload = {"address": address_list}
        return self.post_json_response(url, payload=payload)

    def batch_get_ens_address(self, ens_name_list):
        url = f"{self.ENS_SERVICE_HOST}/v1/ens/batch/name"
        payload = {"name": ens_name_list}
        return self.post_json_response(url, payload=payload)
