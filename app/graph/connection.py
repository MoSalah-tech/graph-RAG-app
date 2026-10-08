import truststore
truststore.inject_into_ssl()

from neo4j import GraphDatabase
from langchain_neo4j import Neo4jGraph
from app.core.config import settings

_driver = None
_graph = None


def get_driver():
    """Raw Neo4j driver — for batch loading with execute_query."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        )
    return _driver


def get_graph() -> Neo4jGraph:
    """LangChain wrapper — for agent queries and schema operations."""
    global _graph
    if _graph is None:
        _graph = Neo4jGraph(
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
            database=settings.NEO4J_DATABASE,
        )
    return _graph