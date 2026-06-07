import os
import re

# Classification constants
STUB = "STUB"
PLACEHOLDER = "PLACEHOLDER"
RETURN_EMPTY = "RETURN_EMPTY"
PASS_STUB = "PASS_STUB"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
TODO = "TODO"
UNWIRED_ROUTE = "UNWIRED_ROUTE"
SAFE_ENDPOINT = "SAFE_ENDPOINT"
RISKY_ENDPOINT = "RISKY_ENDPOINT"

# Directory patterns to walk
DIRS_TO_AUDIT = [
    "api/", "providers/", "search/", "store/", "models/", 
    "pipeline/", "ingest/", "industries/", "web/static/js/", "web/templates/"
]

# Patterns
PATTERNS = {
    STUB: [r"provider_stub", r"StubProvider", r"\"stub\""],
    PLACEHOLDER: [r"\{\{.*\}\}", r"placeholder", r"TODO: implementation"],
    RETURN_EMPTY: [r"return \[\]", r"return \{\}"],
    PASS_STUB: [r"pass\s*#", r"^\s*pass\s*$"],
    NOT_IMPLEMENTED: [r"raise NotImplementedError", r"NotImplementedError"],
    TODO: [r"TODO", r"FIXME"],
}

def audit():
    counts = {
        "STUB_COUNT": 0,
        "PLACEHOLDER_ENDPOINT_COUNT": 0,
        "RETURN_EMPTY_PROVIDER_COUNT": 0,
        "PROVIDER_STUB_COUNT": 0,
        "PASS_COUNT": 0,
        "NOT_IMPLEMENTED_COUNT": 0,
        "TODO_COUNT": 0,
        "UNWIRED_ROUTE_COUNT": 0,
        "SAFE_ENDPOINTS_PRESENT_COUNT": 0,
        "RISKY_LIVE_ENDPOINTS_COUNT": 0
    }
    
    findings = []

    for root_dir in DIRS_TO_AUDIT:
        if not os.path.exists(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith((".py", ".js", ".html", ".sh")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                line_num = i + 1
                                content = line.strip()
                                
                                # Classification logic
                                if "provider_stub" in content:
                                    counts["PROVIDER_STUB_COUNT"] += 1
                                    findings.append((file_path, line_num, "PROVIDER_STUB", "reasoning provider stub found"))
                                
                                if "return []" in content and "providers/" in file_path:
                                    counts["RETURN_EMPTY_PROVIDER_COUNT"] += 1
                                    findings.append((file_path, line_num, "RETURN_EMPTY_PROVIDER", "Provider search() returns []"))

                                if re.search(r"^\s*pass\s*$", content) and "ingest/oidc.py" in file_path:
                                    counts["PASS_COUNT"] += 1
                                    findings.append((file_path, line_num, "PASS_BLOCKER", "pass found in ingest/oidc.py"))

                                if "NotImplementedError" in content:
                                    counts["NOT_IMPLEMENTED_COUNT"] += 1
                                    findings.append((file_path, line_num, "NOT_IMPLEMENTED", "NotImplementedError found"))

                                if "TODO" in content.upper():
                                    counts["TODO_COUNT"] += 1
                                    findings.append((file_path, line_num, "TODO", "TODO found"))

                                # Endpoint checks
                                if "@app.route" in content or "@blueprint.route" in content or "@app.get" in content:
                                    # Expanded safe list including orchestration and research
                                    safe_routes = [
                                        "/health", "/usage", "/opportunities", "/history", "/industries",
                                        "/why-three", "/research", "/batches", "/batch", "/_surface", "/favicon.ico"
                                    ]
                                    risky_routes = ["/jobs", "/ingest", "/demo", "/search"]
                                    
                                    if any(safe in content for safe in safe_routes):
                                        counts["SAFE_ENDPOINTS_PRESENT_COUNT"] += 1
                                    elif any(risky in content for risky in risky_routes):
                                        counts["RISKY_LIVE_ENDPOINTS_COUNT"] += 1
                                    elif content.strip() == "@app.route(\"/\")" or content.strip() == "@app.get(\"/\")":
                                        # Root index is safe
                                        counts["SAFE_ENDPOINTS_PRESENT_COUNT"] += 1
                                    else:
                                        counts["UNWIRED_ROUTE_COUNT"] += 1
                                        findings.append((file_path, line_num, "UNWIRED_ROUTE", f"Unwired or undocumented route found: {content}"))
                                        
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

    # Final summary print
    for key, value in counts.items():
        print(f"{key}: {value}")
    
    print("\nFINDINGS:")
    for f in findings:
        print(f"{f[0]}:{f[1]} [{f[2]}] {f[3]}")

if __name__ == "__main__":
    audit()
