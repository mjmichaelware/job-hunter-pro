from flask import Flask, jsonify
import psycopg2
from serpapi import GoogleSearch
import os

app = Flask(__name__)
SERPAPI_KEY = "4c8b0ddc7564d6d503222cc3b0c54103d591641c075d32b10d6dcc9b8ac49612"
DB_URL = "postgresql://postgres.yegricugzqbmoziycfnt:9514883112199@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        search = GoogleSearch({"engine": "google_jobs", "q": "restaurant server cook", "location": "84115", "lrad": "4", "api_key": SERPAPI_KEY})
        jobs = search.get_dict().get("jobs_results", [])
        for j in jobs:
            cur.execute("INSERT INTO jobs (job_id, title, company, apply_url) VALUES (%s, %s, %s, %s) ON CONFLICT (job_id) DO NOTHING", 
                       (str(j.get("job_id", j.get("title"))), j.get("title"), j.get("company_name"), j.get("apply_link")))
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"status": "complete", "added": len(jobs)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
