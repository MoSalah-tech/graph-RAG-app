# Node labels
NODE_LABELS = [
    "Entity",       # All entities (Company, Person, Country, etc.)
    "Document",     # Source filing chunks
    "Ticker",       # Company tickers
]

# Relationship types (from the dataset)
RELATIONSHIP_TYPES = [
    "DISCLOSES",
    "OPERATES_IN",
    "SUPPLIES_TO",
    "CUSTOMER_OF",
    "COMPETES_WITH",
    "OWNS",
    "SUBSIDIARY_OF",
    "OFFICER_OF",
    "DIRECTOR_OF",
    "HQ_IN",
    "IN_SECTOR",
    "RELATED_TO",
]

# Index properties
ENTITY_INDEX = "entity_name_idx"
TICKER_INDEX = "ticker_idx"
YEAR_INDEX = "year_idx"