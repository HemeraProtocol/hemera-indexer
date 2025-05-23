import json
import logging
import os
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from hemera.common.models.metrics_persistence import MetricsPersistence
from hemera.common.utils.file_utils import write_to_file

logger = logging.getLogger(__name__)


class BasePersistence(object):

    def __init__(self, instance_name):
        self.instance_name = instance_name

    def load(self) -> dict:
        pass

    def save(self, metrics: dict):
        pass

    def init(self):
        pass


class PostgresPersistence(BasePersistence):

    def __init__(self, instance_name, service):
        super().__init__(instance_name)
        self.service = service

    def load(self):
        session = self.service.get_service_session()
        try:
            metrics = (
                session.query(MetricsPersistence.metrics)
                .filter(MetricsPersistence.instance == self.instance_name)
                .scalar()
            )
        except Exception as e:
            raise e
        finally:
            session.close()
        if metrics is not None:
            return metrics
        return {}

    def save(self, metrics: dict):
        session = self.service.get_service_session()
        try:
            conflict_args = {
                "index_elements": [MetricsPersistence.instance],
                "set_": {
                    "metrics": metrics,
                    "update_time": func.to_timestamp(int(datetime.now(timezone.utc).timestamp())),
                },
            }

            statement = (
                insert(MetricsPersistence)
                .values(
                    {
                        "instance": self.instance_name,
                        "metrics": metrics,
                    }
                )
                .on_conflict_do_update(**conflict_args)
            )
            session.execute(statement)
            session.commit()

        except Exception as e:
            raise e

        finally:
            session.close()

    def init(self):
        session = self.service.get_service_session()
        try:
            metrics = (
                session.query(MetricsPersistence).filter(MetricsPersistence.instance == self.instance_name).first()
            )

            if metrics:
                session.delete(metrics)
                session.commit()
        finally:
            session.close()


class FilePersistence(BasePersistence):

    def __init__(self, instance_name):
        super().__init__(instance_name)

    def load(self):
        if not os.path.isfile(self.instance_name):
            return {}
        with open(self.instance_name, "r") as json_file:
            return json.load(json_file)

    def save(self, metrics: dict):
        write_to_file(self.instance_name, json.dumps(metrics))

    def init(self):
        if os.path.isfile(self.instance_name):
            os.remove(self.instance_name)


def init_persistence(instance_name: str, persistence_type: str, config: dict) -> BasePersistence:
    if persistence_type == "postgres":
        try:
            service = config["db_service"]
        except KeyError:
            raise ValueError(f"postgresql persistence loader must provide pg config.")
        return PostgresPersistence(instance_name, service)

    elif persistence_type == "file":
        return FilePersistence(instance_name)

    else:
        raise ValueError("Unable to determine persistence type: " + persistence_type)
