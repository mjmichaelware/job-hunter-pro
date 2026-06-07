import os, psycopg2, sys
from serpapi import GoogleSearch

# Check Database Connection
try:
    print("DEBUG: Checking Database...")
    conn = psycopg2.connect("postgresql://postgres.yegricugzqbmoziycfnt:9514883112199@aws-1-us-east-2.pooler.supabase.com:6543/postgres")
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM jobs;")
    print(f"DEBUG: Current Job Count in DB: {cur.fetchone()[0]}")
    cur.close(); conn.close()
except Exception as e:
    print(f"ERROR: DB Connection Failed: {e}")

# Check SerpApi Key and Connection
API_KEY = "4c8b0ddc7564d6d503222cc3b0c54103d591641c075d32b10d6dcc9b8ac49612"
if len(API_KEY) < 32: print("WARNING: API Key seems too short!")

print("DEBUG: Testing SerpApi Query...")
search = GoogleSearch({"engine": "google_jobs", "q": "Hospitality in Salt Lake City", "api_key": API_KEY})
results = search.get_dict()
if "error" in results:
    print(f"ERROR: SerpApi returned: {results['error']}")
else:
    print(f"SUCCESS: Found {len(results.get('jobs_results', []))} jobs via API")
