from langchain_neo4j import Neo4jVector
from langchain_core.documents import Document

from app.graph.connection import get_graph
from app.services.embedding import get_embeddings


def index_chunks(chunks: list[Document]):
    """
    Embed filing chunks with Voyage AI and store them in Neo4j.

    Creates a vector index on Document nodes so we can do
    semantic search over the raw text later.
    """
    graph = get_graph()
    embeddings = get_embeddings()

    Neo4jVector.from_documents(
        documents=chunks,
        embedding=embeddings,
        graph=graph,
        node_label="Document",
        text_node_property="text",
        embedding_node_property="embedding",
        index_name="filing_chunks",
    )
    print(f"  indexed {len(chunks)} chunks with Voyage AI")