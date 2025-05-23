#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from collections import defaultdict

from prometheus_client import Counter, Gauge, start_http_server

from hemera.indexer.utils.metrics_persistence import BasePersistence

METRICS_CLIENT_PORT = int(os.environ.get("METRICS_CLIENT_PORT", "9200"))


class MetricsCollector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, instance_name: str, persistence: BasePersistence):
        if hasattr(self, "_initialized"):
            return
        start_http_server(METRICS_CLIENT_PORT)

        self.instance_name = instance_name
        self.persistence = persistence

        self._metrics_definition()
        self._load_from_persistence(self.persistence.load())

        self._initialized = True

    def _metrics_definition(self):
        self.last_sync_record = Gauge("last_sync_record", "The last synced block number", ["instance"])

        self.failure_batch_counter = Counter("failure_batch_counter", "Total number of failed index", ["instance"])

        self.indexed_domains = Counter("indexed_domains", "Total number of indexed domains", ["instance", "domain"])

        self.exported_domains = Counter(
            "exported_domains", "Total number of exported domains", ["instance", "domain", "status"]
        )

        self.total_processing_duration = Gauge(
            "total_processing_duration",
            "Total time spent processing each block range in milliseconds",
            ["instance"],
        )

        self.job_processing_duration = Gauge(
            "job_processing_duration",
            "Time spent in each sub-job processing block range in milliseconds",
            ["instance", "job_name"],
        )

        self.export_domains_processing_duration = Gauge(
            "export_domains_processing_duration",
            "Time spent in each sub-job processing block range in milliseconds",
            ["instance", "domains"],
        )

        self.instance_shutdown = Counter(
            "instance_shutdown",
            "Instance shutdown times including mannual and encounter error",
            ["instance"],
        )

        self.job_processing_retry = Counter(
            "job_processing_retry",
            "Retry times in sub-job processing block range",
            ["instance", "job_name"],
        )

    def _load_from_persistence(self, metrics: dict):
        for metric in metrics.keys():
            if hasattr(self, metric):
                collector = getattr(self, metric)
                for indicator in metrics[metric]:
                    label = indicator["label"]

                    if type(collector) is Counter:
                        collector.labels(*label).inc(indicator["value"])
                    elif type(collector) is Gauge:
                        collector.labels(*label).set(indicator["value"])
                    else:
                        raise TypeError(f"Unsupported collector type: {type(collector)}")

    def _wrap_metrics(self) -> dict:
        metrics = defaultdict(list)

        for labels, value in self.failure_batch_counter._metrics.items():
            metrics["failure_batch_counter"].append({"label": labels, "value": value._value.get()})

        for labels, value in self.instance_shutdown._metrics.items():
            metrics["instance_shutdown"].append({"label": labels, "value": value._value.get()})

        for labels, value in self.job_processing_retry._metrics.items():
            metrics["job_processing_retry"].append({"label": labels, "value": value._value.get()})

        return metrics

    def update_last_sync_record(self, last_sync_record: int):
        last_record = self.last_sync_record.labels(instance=self.instance_name)._value.get()
        if last_record < last_sync_record:
            self.last_sync_record.labels(instance=self.instance_name).set(last_sync_record)

    def update_failure_batch_counter(self):
        self.failure_batch_counter.labels(instance=self.instance_name).inc(1)

    def update_indexed_domains(self, domain: str, amount: int):
        self.indexed_domains.labels(instance=self.instance_name, domain=domain).inc(amount)

    def update_exported_domains(self, domain: str, status: str, amount: int):
        self.exported_domains.labels(instance=self.instance_name, domain=domain, status=status).inc(amount)

    def update_total_processing_duration(self, duration: int):
        self.total_processing_duration.labels(instance=self.instance_name).set(duration)

    def update_job_processing_duration(self, job_name: str, duration: int):
        self.job_processing_duration.labels(instance=self.instance_name, job_name=job_name).set(duration)

    def update_export_domains_processing_duration(self, domains: str, duration: int):
        self.export_domains_processing_duration.labels(instance=self.instance_name, domains=domains).set(duration)

    def update_instance_shutdown(self):
        self.instance_shutdown.labels(instance=self.instance_name).inc(1)
        self.persistence.save(self._wrap_metrics())

    def update_job_processing_retry(self, job_name: str, retry: int):
        self.job_processing_retry.labels(instance=self.instance_name, job_name=job_name).inc(retry)
        self.persistence.save(self._wrap_metrics())
