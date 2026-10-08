from datetime import datetime
from app.graph.connection import get_driver


def save_fact(user_id: str, fact: str) -> None:
    driver = get_driver()
    driver.execute_query(
        """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.created_at = $ts
        CREATE (u)-[:KNOWS]->(f:Fact {text: $fact, created_at: $ts})
        """,
        user_id=user_id,
        fact=fact,
        ts=datetime.utcnow().isoformat(),
    )


def get_facts(user_id: str, limit: int = 20) -> list[str]:
    driver = get_driver()
    records, _, _ = driver.execute_query(
        """
        MATCH (u:User {id: $user_id})-[:KNOWS]->(f:Fact)
        RETURN f.text AS text
        ORDER BY f.created_at DESC
        LIMIT $limit
        """,
        user_id=user_id,
        limit=limit,
    )
    return [r["text"] for r in records]