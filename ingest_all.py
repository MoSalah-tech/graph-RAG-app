import sys
import time
from app.graph.ingest_sec import fetch_10k_text
from app.graph.extract import split_text, extract_graph_documents
from app.graph.loader import load_graph_documents, refresh_schema
from app.graph.vector import index_chunks

TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]


def ingest(ticker: str):
    print(f"\n{'='*50}\n{ticker}\n{'='*50}")

    text = fetch_10k_text(ticker)
    if not text:
        return

    chunks = split_text(text, ticker)
    print(f"  split into {len(chunks)} chunks")

    graph_docs = extract_graph_documents(chunks)
    print(f"  extracted {len(graph_docs)} graph documents")

    load_graph_documents(graph_docs)

    index_chunks(chunks)

    time.sleep(20)  # be gentle with the free tiers


def main():
    for ticker in TICKERS:
        ingest(ticker)

    print("\nRefreshing schema...")
    schema = refresh_schema()
    print(schema)
    print("\nDone.")


if __name__ == "__main__":
    main()