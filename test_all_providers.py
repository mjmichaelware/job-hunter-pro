import os, requests
from pathlib import Path

env_path = Path.home() / "projects" / "job-hunter-pro" / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k] = v.strip().strip('"').strip("'")

HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

def safe_req(method, url, timeout=12, **kwargs):
    try:
        return requests.request(method, url, timeout=timeout, **kwargs)
    except requests.exceptions.Timeout:
        return "TIMEOUT"
    except Exception as e:
        return f"ERR: {str(e)[:20]}"

def log_result(name, res):
    if res is None:
        print(f"⚪ {name:<28} -> [KEY UNSET]")
        return
    if isinstance(res, str):
        print(f"❌ {name:<28} -> [{res}]")
        return
    status = res.status_code
    if status in [200, 201]:
        print(f"✅ {name:<28} -> [{status} OK]")
    else:
        msg = res.text.replace("\n", " ")[:50]
        print(f"❌ {name:<28} -> [HTTP {status}: {msg}]")

print("\n================ EXHAUSTIVE LIVE API DIAGNOSTIC ================")

# 1. OpenAI
k = os.getenv("OPENAI_API_KEY")
log_result("OpenAI", safe_req("get", "https://api.openai.com/v1/models", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 2. Google Gemini
k = os.getenv("GEMINI_API_KEY")
log_result("Google Gemini", safe_req("get", f"https://generativelanguage.googleapis.com/v1beta/models?key={k}") if k else None)

# 3. Groq
k = os.getenv("GROQ_API_KEY")
log_result("Groq Inference", safe_req("get", "https://api.groq.com/openai/v1/models", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 4. OpenRouter
k = os.getenv("OPENROUTER_API_KEY")
log_result("OpenRouter", safe_req("get", "https://openrouter.ai/api/v1/models", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 5. DeepSeek
k = os.getenv("DEEPSEEK_API_KEY")
log_result("DeepSeek", safe_req("get", "https://api.deepseek.com/models", timeout=15, headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 6. Mistral AI
k = os.getenv("MISTRAL_API_KEY")
log_result("Mistral AI", safe_req("get", "https://api.mistral.ai/v1/models", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 7. NVIDIA NIM
k = os.getenv("NVIDIA_API_KEY")
log_result("NVIDIA NIM", safe_req("get", "https://integrate.api.nvidia.com/v1/models", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 8. Together AI
k = os.getenv("TOGETHER_AI_API_KEY")
log_result("Together AI", safe_req("get", "https://api.together.xyz/v1/models", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 9. Cerebras
k = os.getenv("CEREBRAS_API_KEY")
log_result("Cerebras", safe_req("get", "https://api.cerebras.ai/v1/models", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 10. SerpAPI
k = os.getenv("SERPAPI_KEY")
log_result("SerpAPI", safe_req("get", f"https://serpapi.com/search.json?q=test&api_key={k}") if k else None)

# 11. Jina AI
k = os.getenv("JINA_API_KEY")
log_result("Jina Reader", safe_req("get", "https://r.jina.ai/https://example.com", headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 12. Context7
k = os.getenv("CONTEXT7_API_KEY")
log_result("Context7", safe_req("post", "https://context7.com/api/v1/search", json={"query": "software engineering"}, headers={**HEADERS, "Authorization": f"Bearer {k}"}) if k else None)

# 13. Adzuna
app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
log_result("Adzuna Jobs", safe_req("get", f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={app_id}&app_key={app_key}&results_per_page=1") if app_id and app_key else None)

# 14. USAJobs
k, email = os.getenv("USAJOBS_API_KEY"), os.getenv("USAJOBS_EMAIL", "developer@jobhunter.pro")
log_result("USAJobs", safe_req("get", "https://data.usajobs.gov/api/search?Keyword=Software", headers={"Host": "data.usajobs.gov", "User-Agent": email, "Authorization-Key": k}) if k else None)

# 15. Jooble
k = os.getenv("JOOBLE_API_KEY")
log_result("Jooble Jobs", safe_req("post", f"https://jooble.org/api/{k}", json={"keywords": "software", "location": "Remote"}, headers=HEADERS) if k else None)

# 16. The Muse (No extra headers)
k = os.getenv("THEMUSE_API_KEY")
log_result("The Muse", safe_req("get", f"https://www.themuse.com/api/v2/jobs?page=1" + (f"&api_key={k}" if k else "")))

# 17. Utah Open Data
token = os.getenv("UTAH_OPEN_DATA_APP_TOKEN")
log_result("Utah Open Data", safe_req("get", "https://data.utah.gov/resource/8j2c-23k4.json?$limit=1", timeout=15, headers={"X-App-Token": token} if token else None))

# 18. Pinecone
k = os.getenv("PINECONE_API_KEY")
log_result("Pinecone Vector DB", safe_req("get", "https://api.pinecone.io/indexes", headers={**HEADERS, "Api-Key": k}) if k else None)

print("================================================================\n")
