import json
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
TAXONOMY_FILE = BASE_DIR / "config" / "search_taxonomy.json"

class QueryBuilder:
    def __init__(self, taxonomy_path: Path = TAXONOMY_FILE):
        with open(taxonomy_path, 'r') as f:
            self._taxonomy = json.load(f)

    def get_queries(self, discovery_mode: str = "all") -> List[str]:
        """
        Generates a list of search queries based on the discovery mode.
        """
        queries = []
        role_families = self._taxonomy.get("role_families", {})
        global_expansions = self._taxonomy.get("global_expansions", [])

        target_families = []
        if discovery_mode == "all":
            target_families = role_families.keys()
        elif discovery_mode in role_families:
            target_families = [discovery_mode]

        for family in target_families:
            family_data = role_families.get(family, {})
            keywords = family_data.get("keywords", [])
            expansions = family_data.get("expansions", [])
            
            for keyword in keywords:
                queries.append(f"{keyword}")
                for expansion in expansions:
                    queries.append(f"{expansion} {keyword}")

        # Add global expansions to all keywords
        expanded_queries = []
        for query in queries:
            for expansion in global_expansions:
                expanded_queries.append(f"{query} {expansion}")
        
        # Add base keywords as well
        expanded_queries.extend(queries)

        # Return a unique list
        return list(dict.fromkeys(expanded_queries))

def get_query_builder() -> QueryBuilder:
    return QueryBuilder()
