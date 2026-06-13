import requests

print("--- DEBUG: Fetching Data from Aggregator ---")
try:
    res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
    data = res.json().get('data', [])
    print(f"DEBUG: Found {len(data)} total jobs from aggregator.")
    
    # Print the location of the first 5 jobs to see if SLC/Utah exists
    for i, item in enumerate(data[:5]):
        print(f"Job {i+1}: {item.get('title')} | Location: {item.get('location')}")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
