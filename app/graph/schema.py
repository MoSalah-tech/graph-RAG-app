NODE_LABELS = ["Company", "Person", "Country", "Sector"]

RELATIONSHIP_TYPES = [
    "SUPPLIES_TO",      # Company -> Company
    "CUSTOMER_OF",      # Company -> Company
    "COMPETES_WITH",    # Company -> Company
    "OWNS",             # Company -> Company
    "SUBSIDIARY_OF",    # Company -> Company
    "OFFICER_OF",       # Person  -> Company
    "DIRECTOR_OF",      # Person  -> Company
    "HQ_IN",            # Company -> Country
    "OPERATES_IN",      # Company -> Country
    "IN_SECTOR",        # Company -> Sector
]