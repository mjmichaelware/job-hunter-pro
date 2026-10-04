#!/bin/bash
set -e

ENV_FILE="$HOME/projects/job-hunter-pro/.env"
mkdir -p "$(dirname "$ENV_FILE")"
touch "$ENV_FILE"

echo "=================================================================="
echo "      JOB HUNTER PRO - EXHAUSTIVE PROVIDER & KEY WIZARD          "
echo "=================================================================="
echo "Press ENTER to skip any key you do not have right now."
echo ""

prompt_key() {
  local var_name="$1"
  local provider_label="$2"
  
  local existing_val=$(grep "^${var_name}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
  
  if [ -n "$existing_val" ]; then
    echo -n "🔑 $provider_label [$var_name] (Set): "
  else
    echo -n "🔑 $provider_label [$var_name]: "
  fi
  
  read -r user_input
  
  if [ -n "$user_input" ]; then
    sed -i "/^${var_name}=/d" "$ENV_FILE" 2>/dev/null || true
    echo "${var_name}=${user_input}" >> "$ENV_FILE"
    echo "   ↳ Updated $var_name"
  fi
}

# --- 1. REASONING & LLM PROVIDERS ---
echo "--- [1/6] REASONING & LLM PROVIDERS ---"
prompt_key "OPENAI_API_KEY" "OpenAI API"
prompt_key "OPENAI_API_KEY_1" "OpenAI Primary Key"
prompt_key "OPENAI_API_KEY_2" "OpenAI Secondary Key"
prompt_key "ANTHROPIC_API_KEY" "Anthropic Claude API"
prompt_key "GEMINI_API_KEY" "Google Gemini API"
prompt_key "GOOGLE_API_KEY_1" "Google AI Studio Key 1"
prompt_key "GOOGLE_API_KEY_2" "Google AI Studio Key 2"
prompt_key "GROQ_API_KEY" "Groq API Key"
prompt_key "GROQ_API_KEY_1" "Groq API Key 1"
prompt_key "GROQ_API_KEY_2" "Groq API Key 2"
prompt_key "XAI_API_KEY" "xAI (Grok) API"
prompt_key "OPENROUTER_API_KEY" "OpenRouter Unified API"
prompt_key "OPENROUTER_API_KEY_1" "OpenRouter Key 1"
prompt_key "OPENROUTER_API_KEY_2" "OpenRouter Key 2"
prompt_key "DEEPSEEK_API_KEY" "DeepSeek API"
prompt_key "MISTRAL_API_KEY" "Mistral AI API"
prompt_key "NVIDIA_API_KEY" "NVIDIA NIM API Key"
prompt_key "NVIDIA_API_KEY_1" "NVIDIA NIM Key 1"
prompt_key "NVIDIA_API_KEY_2" "NVIDIA NIM Key 2"
prompt_key "TOGETHER_AI_API_KEY" "Together AI API"
prompt_key "CEREBRAS_API_KEY" "Cerebras API"
prompt_key "GITHUB_MODELS_TOKEN" "GitHub Models API Token"

# --- 2. SERP & SEARCH AGGREGATORS ---
echo ""
echo "--- [2/6] SERP & SEARCH AGGREGATORS ---"
prompt_key "SERPAPI_KEY" "SerpAPI Key"
prompt_key "JINA_API_KEY" "Jina AI Deep Scraper API"
prompt_key "CONTEXT7_API_KEY" "Context7 Search API"

# --- 3. PRIMARY & AGGREGATED JOB BOARD PROVIDERS ---
echo ""
echo "--- [3/6] PRIMARY JOB BOARDS ---"
prompt_key "ADZUNA_APP_ID" "Adzuna App ID"
prompt_key "ADZUNA_APP_KEY" "Adzuna App Key"
prompt_key "USAJOBS_API_KEY" "USAJobs API Key"
prompt_key "USAJOBS_EMAIL" "USAJobs Email Account"
prompt_key "JOOBLE_API_KEY" "Jooble API Key"
prompt_key "CAREERJET_AFFID" "Careerjet Affiliate ID"
prompt_key "THEMUSE_API_KEY" "The Muse API Key"
prompt_key "CAREERONESTOP_KEY" "CareerOneStop API Key"
prompt_key "ARBEITNOW_API_KEY" "Arbeitnow API Key (Optional)"
prompt_key "REMOTIVE_API_KEY" "Remotive API Key (Optional)"
prompt_key "REMOTEOK_API_KEY" "RemoteOK API Key (Optional)"
prompt_key "JOBICY_API_KEY" "Jobicy API Key (Optional)"

# --- 4. ATS & DIRECT RECRUITER APIS ---
echo ""
echo "--- [4/6] ATS DIRECT PLATFORMS ---"
prompt_key "GREENHOUSE_API_KEY" "Greenhouse Harvest API"
prompt_key "LEVER_API_KEY" "Lever API Key"
prompt_key "ASHBY_API_KEY" "Ashby API Key"

# --- 5. GEOSPATIAL & LOCAL INTELLIGENCE ---
echo ""
echo "--- [5/6] GEOSPATIAL & PLACES APIS ---"
prompt_key "GOOGLE_MAPS_API_KEY" "Google Maps Platform Key"
prompt_key "FOURSQUARE_API_KEY" "Foursquare Places API Key"
prompt_key "YELP_API_KEY" "Yelp Fusion API Key"

# --- 6. PUBLIC DATA, VECTOR STORES & INFRASTRUCTURE ---
echo ""
echo "--- [6/6] PUBLIC DATA & VECTOR DB ---"
prompt_key "UTAH_OPEN_DATA_APP_TOKEN" "Utah Open Data Socrata Token"
prompt_key "DATA_GOV_API_KEY" "Data.gov / USAspending Key"
prompt_key "PINECONE_API_KEY" "Pinecone Vector DB Key"

echo ""
echo "=================================================================="
echo "✅ Configuration recorded in: $ENV_FILE"
echo "=================================================================="
