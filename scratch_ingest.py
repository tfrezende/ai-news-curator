# scratch_ingest.py  ← add to .gitignore, delete when done
import logging
from src.config import settings
from src.storage.sqlite import SQLiteStorage
from src.storage.chroma import ChromaStorage
from src.pipeline.ingest import IngestPipeline

logging.basicConfig(
    level="INFO", format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

sql = SQLiteStorage(db_path=settings.SQLITE_DB_PATH)
chroma = ChromaStorage(db_path=settings.CHROMA_DB_PATH)
pipeline = IngestPipeline(sql_storage=sql, chroma_storage=chroma)
pipeline.run()

# verify SQLite
articles = sql.get_recent_articles(limit=5)
for a in articles:
    print(f"[SQLite] {a.title} — {a.source}")

# verify ChromaDB
results = chroma.search_articles("open source software")
for r in results:
    print(f"[Chroma] {r['title']} (score: {r['score']})")
