## To set up custom jobs, follow these steps:

1. Add feature_id to the `FeatureType` class in `indexer.modules.custom.feature_type` following the indexing guidelines.
2. Create a package for your jobs within `indexer/modules/custom`.
3. If needed, define your intermediary table model in `indexer/modules/custom/{yourPackage}/models`, naming it with the
   prefix 'feature_'.
4. Create a dataclass for your middle table in the respective job package.
5. Create a data class in `indexer/modules/custom/{yourPackage}/domain` and add an entry to `model_domain_mapping`
   in `common.models.all_features_value_records.AllFeatureValueRecords` to link it properly.
6. Optionally, run the Alembic command **alembic -c resource/hemera.ini revision --autogenerate -m "description"** to
   generate migrations for your middle table. Rename the migration file in `migrations/versions` according to the
   indexing
   scheme.

### Points to Note:

1. Entities in the `models` directory relate to the database and require setting primary keys, indexes, etc.
   The `model_domain_mapping` maps the `dataclass` entities to database tables and includes settings for update
   strategies.
2. Entities in the `domain` directory inherit from either `Domain` or `FilterData`, depending on whether your job
   requires preliminary filtering.
3. The output within the `job` is handled through the method `self._collect_item`, where each entity instance is added
   one by one.
