from serpapi import GoogleSearch
import os

API_KEY = "4c8b0ddc7564d6d503222cc3b0c54103d591641c075d32b10d6dcc9b8ac49612"

try:
    search = GoogleSearch({"engine": "google_jobs", "q": "Hospitality in Salt Lake City", "api_key": API_KEY})
    results = search.get_dict()
    
    if "error" in results:
        print(f"❌ API ERROR: {results['error']}")
    else:
        jobs = results.get("jobs_results", [])
        print(f"✅ API SUCCESS: Found {len(jobs)} jobs.")
        for job in jobs[:3]:
            print(f"- {job.get('title')} at {job.get('company_name')}")
except Exception as e:
    print(f"❌ SCRIPT ERROR: {e}")
