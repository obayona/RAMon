# Pinecone importer

It loads the CSV file `products_preprocessed.csv` with products and upload it to the `ramon-products` Pinecone index. You should define a `.env` file with the same variables as `.env.example`

```bash
python import_to_pinecone.py
```

Use the following script to perform a query on Pinecone to check the import worked

```bash
python query_pinecone.py
```
