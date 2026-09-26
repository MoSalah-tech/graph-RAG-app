from app.graph.connection import get_graph


def load_graph_documents(graph_documents, clear_existing: bool = False):
    graph = get_graph()

    if clear_existing:
        graph.query("MATCH (n) DETACH DELETE n")
        print("  cleared existing graph")

    graph.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True,
    )
    print(f"  loaded {len(graph_documents)} graph documents")


def refresh_schema() -> str:
    graph = get_graph()
    graph.refresh_schema()
    return graph.schema