from typing import List, Dict, Any, Callable

class FederatedSearch:
    def __init__(self, provider_registry: Dict[str, Callable], budget_guard):
        self.provider_registry = provider_registry
        self.budget_guard = budget_guard

    def _generate_broad_queries(self, base_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        # For "all_jobs" mode, simply return the base query for each provider
        queries = []
        for provider_name in self.provider_registry.keys():
            queries.append({"provider": provider_name, "query": base_query})
        return queries

    def _generate_seeded_queries(self, base_query: Dict[str, Any], industry_seeds: List[str]) -> List[Dict[str, Any]]:
        # Industry-seeded mode: generate queries with industry hints
        queries = []
        for provider_name in self.provider_registry.keys():
            for seed in industry_seeds:
                # Add industry as a hint, not a hard exclusion
                seeded_query = base_query.copy()
                seeded_query["industry_hint"] = seed
                queries.append({"provider": provider_name, "query": seeded_query})
        return queries

    def plan_queries(self, mode: str, base_query: Dict[str, Any], industry_seeds: List[str] = None) -> List[Dict[str, Any]]:
        if mode == "all_jobs":
            return self._generate_broad_queries(base_query)
        elif mode == "industry_seeded" and industry_seeds:
            return self._generate_seeded_queries(base_query, industry_seeds)
        else:
            raise ValueError("Invalid mode or missing industry seeds for 'industry_seeded' mode.")

    def execute_query_plan(self, query_plan: List[Dict[str, Any]]) -> List[Any]:
        results = []
        for plan_item in query_plan:
            provider_name = plan_item["provider"]
            query = plan_item["query"]
            
            # Simulate a cost
            simulated_cost = 1.0 

            if self.budget_guard.can_afford(provider_name, simulated_cost):
                # In S7 proof, we don't actually call the provider. 
                # Just record the transaction and return a dummy result.
                self.budget_guard.record_transaction(provider_name, simulated_cost)
                results.append(f"Result from {provider_name} for query {query}")
            else:
                results.append(f"Query for {provider_name} skipped due to budget.")
        return results
