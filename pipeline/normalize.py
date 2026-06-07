def normalize_job(raw: dict, provider: str = "test") -> dict:
    return {
        "title": raw.get("title", ""),
        "company": raw.get("company", "Unknown"),
        "description": raw.get("description", raw.get("snippet", "")),
        "location": raw.get("location", ""),
        "url": raw.get("url", "https://example.com"),
        "provider": provider,
        "raw_json": raw,
    }
