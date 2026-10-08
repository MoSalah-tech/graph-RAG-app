# app/graph/constraints.py
from app.graph.connection import get_driver

CONSTRAINTS = [
    "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
    "CREATE CONSTRAINT ticker_symbol IF NOT EXISTS FOR (t:Ticker) REQUIRE t.symbol IS UNIQUE",
    "CREATE CONSTRAINT doc_chunk_id IF NOT EXISTS FOR (d:Document) REQUIRE d.chunk_id IS UNIQUE",
    "CREATE INDEX entity_year IF NOT EXISTS FOR (e:Entity) ON (e.year)",
]


def apply_constraints():
    driver = get_driver()
    with driver.session() as session:
        for stmt in CONSTRAINTS:
            try:
                session.run(stmt)
                print(f"  applied: {stmt[:60]}...")
            except Exception as e:
                print(f"  skipped: {e}")
    print("Constraints applied.")