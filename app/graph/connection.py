import truststore
truststore.inject_into_ssl()

from langchain_neo4j import Neo4jGraph
from app.core.config import settings

_graph = None


def get_graph() -> Neo4jGraph:
    global _graph
    if _graph is None:
        _graph = Neo4jGraph(
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
            database=settings.NEO4J_DATABASE,
        )
    return _graph