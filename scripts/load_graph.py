from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyarrow.parquet as pq
from app.graph.connection import get_driver
from app.graph.constraints import apply_constraints

# ---- Find cached Parquet files ----
CACHE_ROOT = Path.home() / ".cache" / "huggingface" / "hub" / "datasets--domyn--FinReflectKG"
parquet_files = sorted(CACHE_ROOT.rglob("*.parquet"))

if not parquet_files:
    raise SystemExit("No Parquet files found. Check the cache path.")

print(f"Found {len(parquet_files)} Parquet files.")
print(f"First: {parquet_files[0].name}")
print(f"Last:  {parquet_files[-1].name}")

# ---- TEST: only first 2 files (~35K rows, ~2 min) ----
# Set to None for the full 103-file load
TEST_FILES = 5
files_to_load = parquet_files[:TEST_FILES] if TEST_FILES else parquet_files

BATCH_SIZE = 1000

LOAD_ENTITIES = """
UNWIND $rows AS row
MERGE (e:Entity {name: row.entity})
ON CREATE SET e.type = row.entity_type, e.created_at = timestamp()
ON MATCH SET e.type = coalesce(e.type, row.entity_type)
"""

LOAD_TICKERS = """
UNWIND $rows AS row
MERGE (t:Ticker {symbol: row.ticker})
ON CREATE SET t.created_at = timestamp()
"""

LOAD_DOCUMENTS = """
UNWIND $rows AS row
MERGE (d:Document {chunk_id: row.chunk_id})
ON CREATE SET
    d.text = row.chunk_text,
    d.ticker = row.ticker,
    d.year = row.year,
    d.source_file = row.source_file,
    d.page_id = row.page_id
"""

LOAD_RELATIONSHIPS = """
UNWIND $rows AS row
MATCH (e:Entity {name: row.entity})
MATCH (t:Entity {name: row.target})
MERGE (e)-[r:RELATED_TO {
    type: row.relationship,
    start_date: row.start_date,
    end_date: row.end_date
}]->(t)
ON CREATE SET r.triplet_id = row.triplet_id, r.extraction_type = row.extraction_type
"""

LINK_ENTITIES_TO_DOCS = """
UNWIND $rows AS row
MATCH (e:Entity {name: row.entity})
MATCH (d:Document {chunk_id: row.chunk_id})
MERGE (e)-[:MENTIONED_IN]->(d)
"""

LINK_TICKER_TO_ENTITY = """
UNWIND $rows AS row
MATCH (t:Ticker {symbol: row.ticker})
MATCH (e:Entity {name: row.entity})
MERGE (t)-[:HAS_ENTITY]->(e)
"""


def load_batches(driver, query, rows):
    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        _, summary, _ = driver.execute_query(query, rows=batch)
        total += summary.counters.nodes_created + summary.counters.relationships_created
    return total


def main():
    print("\n=== Applying constraints ===")
    apply_constraints()
    driver = get_driver()

    totals = {
        "entities": 0, "tickers": 0, "docs": 0,
        "rels": 0, "mentions": 0, "has_entity": 0,
    }

    for idx, path in enumerate(files_to_load, 1):
        print(f"\n=== File {idx}/{len(files_to_load)}: {path.name} ===")
        df = pq.read_table(path).to_pandas()
        print(f"  {len(df):,} rows")

        df["ticker"] = df["ticker"].astype(str).str.lower()
        df["entity"] = df["entity"].astype(str).str.lower()
        df["target"] = df["target"].astype(str).str.lower()

        entities = df[["entity", "entity_type"]].drop_duplicates().to_dict("records")
        n = load_batches(driver, LOAD_ENTITIES, entities)
        totals["entities"] += n
        print(f"  [1/6] Entities: {n}")

        tickers = df[["ticker"]].drop_duplicates().to_dict("records")
        n = load_batches(driver, LOAD_TICKERS, tickers)
        totals["tickers"] += n
        print(f"  [2/6] Tickers: {n}")

        docs = df[["chunk_id", "chunk_text", "ticker", "year",
                   "source_file", "page_id"]].drop_duplicates("chunk_id").to_dict("records")
        n = load_batches(driver, LOAD_DOCUMENTS, docs)
        totals["docs"] += n
        print(f"  [3/6] Documents: {n}")

        rels = df[["entity", "target", "relationship", "start_date", "end_date",
                   "triplet_id", "extraction_type"]].to_dict("records")
        n = load_batches(driver, LOAD_RELATIONSHIPS, rels)
        totals["rels"] += n
        print(f"  [4/6] Relationships: {n}")

        mentions = df[["entity", "chunk_id"]].drop_duplicates().to_dict("records")
        n = load_batches(driver, LINK_ENTITIES_TO_DOCS, mentions)
        totals["mentions"] += n
        print(f"  [5/6] MENTIONED_IN: {n}")

        tick_ent = df[["ticker", "entity"]].drop_duplicates().to_dict("records")
        n = load_batches(driver, LINK_TICKER_TO_ENTITY, tick_ent)
        totals["has_entity"] += n
        print(f"  [6/6] HAS_ENTITY: {n}")

    print("\n=== Totals ===")
    for k, v in totals.items():
        print(f"{k:15} {v}")


if __name__ == "__main__":
    main()