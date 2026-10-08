from fastapi import APIRouter
from app.graph.connection import get_driver

router = APIRouter()


@router.get("/health")
def health():
    try:
        driver = get_driver()
        driver.execute_query("RETURN 1 AS ok")
        return {"status": "healthy", "neo4j": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}