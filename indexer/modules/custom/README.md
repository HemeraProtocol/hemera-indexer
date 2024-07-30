## To set up custom jobs, follow these steps:

1. Add feature_id to the FeatureType class in indexer.modules.custom.feature_type following the indexing guidelines.
2. Create a package for your jobs within indexer/modules/custom.
3. If required, define your middle table model in common/models.
4. Create a dataclass for your middle table in the respective job package.
5. Optionally, run the Alembic command **alembic -c resource/hemera.ini revision --autogenerate -m "description"** to generate migrations for your middle table. Rename the migration file in migrations/versions according to the indexing scheme.
