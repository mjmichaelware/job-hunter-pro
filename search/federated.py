import logging
from typing import List, Dict, Any, Optional
from models import SearchResult
from providers import get_providers_by_type, ProviderType, SearchProvider
from industries import get_all_routes, get_route

logger = logging.getLogger(__name__)

class FederatedSearch:
    def __init__(self, budget_guard, cache_repo):
        self.budget_guard = budget_guard
        self.cache_repo = cache_repo

    def plan_queries(self, industry_keys: List[str] = None) -> List[Dict[str, Any]]:
        """
        Builds an execution plan based on industry routes and provider availability.
        If no industry_keys provided, plans for all registered industries.
        """
        plan = []
        target_industries = []
        
        if industry_keys:
            for key in industry_keys:
                route = get_route(key)
                if route:
                    target_industries.append(route)
        else:
            target_industries = get_all_routes()

        search_providers = get_providers_by_type(ProviderType.SEARCH)
        
        for industry in target_industries:
            for provider in search_providers:
                if provider.is_available():
                    for query in industry.queries:
                        plan.append({
                            "provider": provider.metadata.key,
                            "industry": industry.key,
                            "query": query,
                            "is_free": provider.metadata.requires_api_key is False
                        })
        return plan

    def execute_plan(self, plan: List[Dict[str, Any]]) -> List[SearchResult]:
        """
        Executes the query plan, merging and deduping results.
        Respects budget and utilizes cache.
        """
        all_results = []
        seen_urls = set()

        for item in plan:
            provider_key = item["provider"]
            query = item["query"]
            industry_key = item["industry"]
            
            # 1. Check Cache
            cache_key = self.cache_repo.generate_key(provider_key, query, industry_key)
            cached = self.cache_repo.get_cached_results(cache_key)
            if cached:
                logger.debug(f"Cache Hit: {provider_key} | {query}")
                for r_dict in cached:
                    try:
                        res = SearchResult(**r_dict)
                        if res.url not in seen_urls:
                            all_results.append(res)
                            seen_urls.add(res.url)
                    except Exception as e:
                        logger.error(f"Failed to parse cached result: {e}")
                continue

            # 2. Check Budget
            if not self.budget_guard.can_afford(provider_key):
                logger.info(f"Skipping {provider_key} due to budget.")
                continue

            # 3. Search
            provider = next((p for p in get_providers_by_type(ProviderType.SEARCH) if p.metadata.key == provider_key), None)
            if not provider:
                continue

            try:
                logger.info(f"Searching {provider_key} for '{query}'...")
                results = provider.search(query)
                
                # 4. Record & Cache
                self.budget_guard.record_transaction(provider_key)
                
                # Store in cache (as dicts)
                self.cache_repo.set_cached_results(cache_key, {
                    "provider": provider_key,
                    "query": query,
                    "industry": industry_key,
                    "results": [r.model_dump() for r in results]
                })

                # 5. Merge & Dedupe
                for res in results:
                    if res.url not in seen_urls:
                        all_results.append(res)
                        seen_urls.add(res.url)
                        
            except Exception as e:
                logger.error(f"Provider {provider_key} failed: {e}")
                # Fail closed - don't crash the whole run

        return all_results
