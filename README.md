# hemera_indexer

## Quickstart
configurate your postgresql in alembic.ini
```angular2html
sqlalchemy.url = driver://user:pass@localhost/dbname
```


Start with minimal parameters to export all entities as:
```bash
python hemera.py stream \
-p https://mainnet.infura.io \
-d https://mainnet.infura.io \
-o driver://user:pass@localhost/dbname
```

Export blocks and transactions:
```bash
python hemera.py stream \
-p https://mainnet.infura.io \
-d https://mainnet.infura.io \
-o driver://user:pass@localhost/dbname \
-e block,transaction
```

Export all entities and sink to local as json, csv files
```bash
python hemera.py stream \
-p https://mainnet.infura.io \
-d https://mainnet.infura.io \
-o driver://user:pass@localhost/dbname,jsonfile://your_data_folder/sub_json_folder,csvfile://your_data_folder/sub_csv_folder \
```