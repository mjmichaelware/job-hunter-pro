import os
import urllib.request
import json
from pathlib import Path

# Load .env file manually
env_path = Path.home() / "projects" / "job-hunter-pro" / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

def check_endpoint(name, url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            status = res.getcode()
            if status in [200, 201]:
                print(f"✅ {name:<25} -> [200 OK]")
            else:
                print(f"⚠️ {name:<25} -> Status {status}")
    except urllib.error.HTTPError as e:
        if e.code in [200, 201]:
            print(f"✅ {name:<25} -> [{e.code} OK]")
        else:
            print(f"❌ {name:<25} -> [HTTP {e.code}: {e.reason}]")
    except Exception as e:
        print(f"❌ {name:<25} -> [{type(e).__name__}: {e}]")

print("\n================ LIVE API PROVIDER HEALTH CHECK ================")

# 1. OpenAI
key = os.getenv("OPENAI_API_KEY")
if key:
    check_endpoint("OpenAI", "https://api.openai.com/v1/models", {"Authorization": f"Bearer {key}"})

# 2. Gemini
key = os.getenv("GEMINI_API_KEY")
if key:
    check_endpoint("Google Gemini", f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")

# 3. Groq
key = os.getenv("GROQ_API_KEY")
if key:
    check_endpoint("Groq Inference", "https://api.groq.com/openai/v1/models", {"Authorization": f"Bearer {key}"})

# 4. OpenRouter
key = os.getenv("OPENROUTER_API_KEY")
if key:
    check_endpoint("OpenRouter", "https://openrouter.ai/api/v1/models", {"Authorization": f"Bearer {key}"})

# 5. DeepSeek
key = os.getenv("DEEPSEEK_API_KEY")
if key:
    check_endpoint("DeepSeek", "https://api.deepseek.com/models", {"Authorization": f"Bearer {key}"})

# 6. Mistral AI
key = os.getenv("MISTRAL_API_KEY")
if key:
    check_endpoint("Mistral AI", "https://api.mistral.ai/v1/models", {"Authorization": f"Bearer {key}"})

# 7. NVIDIA NIM
key = os.getenv("NVIDIA_API_KEY")
if key:
    check_endpoint("NVIDIA NIM", "https://integrate.api.nvidia.com/v1/models", {"Authorization": f"Bearer {key}"})

# 8. Together AI
key = os.getenv("TOGETHER_AI_API_KEY")
if key:
    check_endpoint("Together AI", "https://api.together.xyz/v1/models", {"Authorization": f"Bearer {key}"})

# 9. Cerebras
key = os.getenv("CEREBRAS_API_KEY")
if key:
    check_endpoint("Cerebras", "https://api.cerebras.ai/v1/models", {"Authorization": f"Bearer {key}"})

# 10. SerpAPI
key = os.getenv("SERPAPI_KEY")
if key:
    check_endpoint("SerpAPI", f"https://serpapi.com/search.json?q=test&api_key={key}")

# 11. Jina AI
key = os.getenv("JINA_API_KEY")
if key:
    check_endpoint("Jina Reader", "https://r.jina.ai/https://example.com", {"Authorization": f"Bearer {key}"})

# 12. Adzuna
app_id = os.getenv("ADZUNA_APP_ID")
app_key = os.getenv("ADZUNA_APP_KEY")
if app_id and app_key:
    check_endpoint("Adzuna Jobs", f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={app_id}&app_key={app_key}&results_per_page=1")

# 13. Jooble
key = os.getenv("JOOBLE_API_KEY")
if key:
    check_endpoint("Jooble Jobs", f"https://jooble.org/api/{key}")

# 14. The Muse
key = os.getenv("THEMUSE_API_KEY")
if key:
    check_endpoint("The Muse", f"https://www.themuse.com/api/v1/jobs?page=1&api_key={key}")

print("================================================================\n")
