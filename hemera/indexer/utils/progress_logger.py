import logging
from datetime import datetime

from tqdm import tqdm

from hemera.indexer.utils.atomic_counter import AtomicCounter


class TqdmExtraFormat(tqdm):
    """Provides both estimated and actual total time format parameters"""

    @property
    def format_dict(self):
        d = super().format_dict
        d.update(
            total_time=self.format_interval(d["total"] / (d["n"] / d["elapsed"]) if d["elapsed"] and d["n"] else 0),
            current_total_time=self.format_interval(d["elapsed"]),
        )
        return d


class ProgressLogger:
    def __init__(self, name="work", logger=None, log_percentage_step=10, log_item_step=5000):
        self.name = name
        self.total_items = None
        self.start_time = None
        self.end_time = None
        self.counter = AtomicCounter()
        self.log_percentage_step = log_percentage_step
        self.log_items_step = log_item_step
        self.logger = logger if logger else logging.getLogger("ProgressLogger")
        self.pbar = None

    def start(self, total_items=None):
        if self.counter is None:
            self.counter = AtomicCounter()

        self.total_items = total_items
        self.start_time = datetime.now()

        # Initialize progress bar with improved format
        self.pbar = TqdmExtraFormat(
            total=total_items,
            desc=self.name.ljust(35),
            unit="items",
            ncols=104,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] Est: {total_time}, Total: {current_total_time}",
        )

    def track(self, item_count=1):
        processed_items = self.counter.increment(item_count)
        self.pbar.update(item_count)

        if self.total_items is not None and self.total_items > 0:
            percentage = processed_items * 100 / self.total_items
            if percentage > 100:
                self.pbar.set_description(f"{self.name} !!! Over 100%")
        elif self.total_items is None or self.total_items == 0:
            self.pbar.set_description(f"{self.name} ({processed_items} items)")

    def finish(self):
        if self.pbar is not None:
            self.pbar.close()

        self.counter = None
