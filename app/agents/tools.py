import json
from langchain_core.tools import tool
from app.graph.connection import get_driver, get_graph
from app.memory.store import save_fact, get_facts



@tool
def run_cypher(query: str) -> str:
    """Execute a Cypher query against the financial knowledge graph.

    Use this for structured questions about companies, tickers, relationships.
    The graph schema:
      Nodes:
        - Entity {name, type}          # companies, people, financial metrics
        - Ticker {symbol}              # stock tickers (e.g. 'aapl', 'cat')
        - Document {chunk_id, text, ticker, year, source_file}

      Relationships:
        - (Entity)-[:RELATED_TO {type, start_date, end_date}]->(Entity)
        - (Entity)-[:MENTIONED_IN]->(Document)
        - (Ticker)-[:HAS_ENTITY]->(Entity)

    Entity names are lowercase tickers (e.g. 'aapl', 'cat', 'net income').
    """
    try:
        driver = get_driver()
        records, _, _ = driver.execute_query(query)
        if not records:
            return "No results."
        return json.dumps([dict(r) for r in records[:50]], default=str)
    except Exception as e:
        return f"Cypher error: {e}"


@tool
def find_path(entity_a: str, entity_b: str, max_hops: int = 3) -> str:
    """Find how two entities are connected in the graph.

    Use this for questions like 'how is X connected to Y?' or 'what links A and B?'
    Entity names should be lowercase tickers or entity names (e.g. 'aapl', 'cat').
    """
    query = f"""
    MATCH (a:Entity {{name: $a}}), (b:Entity {{name: $b}})
    MATCH path = shortestPath((a)-[:RELATED_TO*1..{max_hops}]-(b))
    RETURN [n IN nodes(path) | n.name] AS path,
           [r IN relationships(path) | r.type] AS relationships,
           length(path) AS hops
    LIMIT 5
    """
    try:
        driver = get_driver()
        records, _, _ = driver.execute_query(query, a=entity_a.lower(), b=entity_b.lower())
        if not records:
            return f"No path found between '{entity_a}' and '{entity_b}' within {max_hops} hops."
        return json.dumps([dict(r) for r in records], default=str)
    except Exception as e:
        return f"Path error: {e}"


@tool
def search_entity(name: str) -> str:
    """Look up an entity by name (fuzzy match). Returns the exact name to use in queries.

    Use this first if you're not sure of the exact entity name.
    """
    query = """
    MATCH (e:Entity)
    WHERE toLower(e.name) CONTAINS toLower($name)
    RETURN e.name AS name, e.type AS type
    LIMIT 10
    """
    try:
        driver = get_driver()
        records, _, _ = driver.execute_query(query, name=name)
        if not records:
            return f"No entities matching '{name}'."
        return json.dumps([dict(r) for r in records])
    except Exception as e:
        return f"Search error: {e}"


@tool
def get_entity_relationships(entity_name: str, limit: int = 20) -> str:
    """Get all relationships from a specific entity. Useful for 'what does X do?'

    Returns what entity X is connected to and how.
    """
    query = """
    MATCH (e:Entity {name: $name})-[r:RELATED_TO]->(other:Entity)
    RETURN r.type AS relationship, other.name AS target, other.type AS target_type
    LIMIT $limit
    """
    try:
        driver = get_driver()
        records, _, _ = driver.execute_query(
            query, name=entity_name.lower(), limit=limit
        )
        if not records:
            return f"No outgoing relationships for '{entity_name}'."
        return json.dumps([dict(r) for r in records], default=str)
    except Exception as e:
        return f"Relationships error: {e}"


ALL_TOOLS = [run_cypher, find_path, search_entity, get_entity_relationships]

def make_memory_tools(user_id: str):
    """Build memory tools bound to a specific user."""

    @tool
    def recall_memory() -> str:
        """Recall facts you previously saved about the current user.

        Use this at the start of a conversation to personalize answers.
        """
        facts = get_facts(user_id)
        if not facts:
            return "No memories saved yet for this user."
        return "Known facts about the user:\n" + "\n".join(f"- {f}" for f in facts)

    @tool
    def save_memory(fact: str) -> str:
        """Save a fact about the user to long-term memory.

        Use this when the user reveals a preference, goal, portfolio holding,
        or anything worth remembering in future conversations.
        """
        save_fact(user_id, fact)
        return f"Saved: {fact}"

    return [recall_memory, save_memory]