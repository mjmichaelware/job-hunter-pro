import os, psycopg2
from flask import Flask, jsonify, render_template_string
from serpapi import GoogleSearch

app = Flask(__name__)

SERPAPI_KEY = "4c8b0ddc7564d6d503222cc3b0c54103d591641c075d32b10d6dcc9b8ac49612"
DB_URL = "postgresql://postgres.yegricugzqbmoziycfnt:9514883112199@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # DEFINITIVE FIX: 
        # Canonical location mapping + Zip Code injected into the query string.
        search = GoogleSearch({
            "engine": "google_jobs", 
            "q": "restaurant jobs 84115", 
            "location": "Salt Lake City, Utah, United States",
            "hl": "en",
            "api_key": SERPAPI_KEY
        })
        
        jobs = search.get_dict().get("jobs_results", [])
        
        if not jobs:
            return jsonify({"status": "error", "message": "Google returned 0 jobs. API parsing empty."})

        for j in jobs:
            job_id = str(j.get("job_id", j.get("title")))
            cur.execute("INSERT INTO jobs (job_id, title, company, apply_url) VALUES (%s, %s, %s, %s) ON CONFLICT (job_id) DO NOTHING", 
                       (job_id, j.get("title"), j.get("company_name"), j.get("apply_link")))
        
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"status": "success", "count": len(jobs)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/get_jobs', methods=['GET'])
def get_jobs():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT title, company, apply_url FROM jobs ORDER BY id DESC LIMIT 50;")
        jobs = [{"title": r[0], "company": r[1], "url": r[2]} for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"status": "success", "data": jobs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/')
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html class="dark">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>body { font-family: 'Inter', sans-serif; }</style>
    </head>
    <body class="bg-slate-950 p-6 text-white min-h-screen">
        <div class="max-w-2xl mx-auto">
            <div class="flex justify-between items-center mb-6 pb-4 border-b border-slate-800">
                <div>
                    <h1 class="text-2xl font-black text-blue-500 tracking-tight">RESTAURANT JOBS</h1>
                    <p class="text-slate-400 text-sm">Target Area: 84115</p>
                </div>
                <button onclick="syncJobs()" class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-4 py-2 rounded-full transition-colors">
                    SYNC NOW
                </button>
            </div>
            
            <div id="status" class="text-slate-400 text-sm mb-6 font-mono">Status: Ready.</div>
            <div id="list" class="grid gap-4"></div>
        </div>

        <script>
            async function loadJobs() {
                const list = document.getElementById('list');
                const status = document.getElementById('status');
                
                try {
                    const res = await fetch('/api/get_jobs');
                    const json = await res.json();
                    
                    if (json.status === "error") {
                        status.innerHTML = `<span class="text-red-500 font-bold">DB Error: ${json.message}</span>`;
                        return;
                    }
                    
                    const data = json.data;
                    if (data.length === 0) {
                        list.innerHTML = '<p class="text-slate-500 text-center mt-10">No jobs in database. Click SYNC NOW.</p>';
                        return;
                    }

                    list.innerHTML = data.map(j => `
                        <div class="bg-slate-900 p-5 rounded-xl border border-slate-700 hover:border-blue-500 transition-all shadow-lg">
                            <h3 class="font-bold text-lg mb-1">${j.title}</h3>
                            <p class="text-blue-400 text-sm font-semibold mb-4">${j.company}</p>
                            <a href="${j.url}" target="_blank" class="bg-blue-600 block text-center py-3 rounded-lg font-bold text-sm hover:bg-blue-500 transition-colors">QUICK APPLY</a>
                        </div>
                    `).join('');
                } catch (e) {
                    status.innerHTML = `<span class="text-red-500 font-bold">Network Error: ${e.message}</span>`;
                }
            }

            async function syncJobs() {
                const status = document.getElementById('status');
                status.innerHTML = '<span class="text-blue-400">Scraping Local Google Jobs... Please wait.</span>';
                
                try {
                    const res = await fetch('/api/scrape', { method: 'POST' });
                    const json = await res.json();
                    
                    if (json.status === "error") {
                        status.innerHTML = `<span class="text-red-500 font-bold">Scrape Error: ${json.message}</span>`;
                        return;
                    }
                    
                    status.innerHTML = `<span class="text-green-400 font-bold">Success! Added ${json.count} new jobs.</span>`;
                    loadJobs();
                } catch (e) {
                    status.innerHTML = `<span class="text-red-500 font-bold">Network Error: ${e.message}</span>`;
                }
            }

            loadJobs();
        </script>
    </body>
    </html>
    """)

handler = app
