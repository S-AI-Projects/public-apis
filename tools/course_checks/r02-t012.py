#!/usr/bin/env python3
"""
R02-T012: Redirect verification for Public APIs catalogue.
Category: Open Data [README.md]
Task: R02-T012 · 2 of 10

Selected entries:
- 10ML Fragrance Index: https://mcp.10ml.com/openapi.json
- 221: https://221.orvlabs.com/documentation
- 49 Gallery Historical Data: https://api.181649.com/docs
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

SELECTED_ENTRIES = [
    {
        "name": "10ML Fragrance Index",
        "url": "https://mcp.10ml.com/openapi.json",
        "line": 1887,
        "category": "Open Data"
    },
    {
        "name": "221",
        "url": "https://221.orvlabs.com/documentation",
        "line": 1888,
        "category": "Open Data"
    },
    {
        "name": "49 Gallery Historical Data",
        "url": "https://api.181649.com/docs",
        "line": 1889,
        "category": "Open Data"
    }
]

# Classification labels
STATUS_OK = "OK (200)"
STATUS_MOVED = "MOVED_PERMANENT (301->200)"
STATUS_REDIRECT_LOOP = "REDIRECT_LOOP"
STATUS_TIMEOUT = "TIMEOUT (Transient Failure)"
STATUS_LOGIN_WALL = "LOGIN_WALL"
STATUS_TRANSIENT_ERROR = "TRANSIENT_FAILURE"

MAX_REDIRECT_BUDGET = 5

class MockResponse:
    def __init__(self, status_code: int, url: str, headers: Optional[Dict[str, str]] = None, is_timeout: bool = False):
        self.status_code = status_code
        self.url = url
        self.headers = headers or {}
        self.is_timeout = is_timeout

def classify_redirect_chain(initial_url: str, steps: List[MockResponse], max_redirects: int = MAX_REDIRECT_BUDGET) -> Dict[str, Any]:
    """
    Classifies a redirect chain given simulated or actual response steps.
    Bounded request budget prevents infinite loops.
    """
    visited_urls = []
    current_url = initial_url
    
    for idx, resp in enumerate(steps):
        if resp.is_timeout:
            return {
                "initial_url": initial_url,
                "status": STATUS_TIMEOUT,
                "final_url": current_url,
                "chain": visited_urls,
                "redirect_count": len(visited_urls),
                "recommendation": "Retain entry. Transient network timeout; do not remove without manual verification."
            }
        
        visited_urls.append(resp.url)
        
        # Check login wall
        login_indicators = ["/login", "/signin", "/auth/", "accounts.google.com", "login.microsoftonline.com", "auth0"]
        if any(ind in resp.url.lower() for ind in login_indicators) or resp.status_code in (401, 403):
            return {
                "initial_url": initial_url,
                "status": STATUS_LOGIN_WALL,
                "final_url": resp.url,
                "chain": visited_urls,
                "redirect_count": len(visited_urls),
                "recommendation": "Login wall or authorization required; review entry auth metadata."
            }
        
        # Check loop
        if visited_urls.count(resp.url) > 1:
            return {
                "initial_url": initial_url,
                "status": STATUS_REDIRECT_LOOP,
                "final_url": resp.url,
                "chain": visited_urls,
                "redirect_count": len(visited_urls),
                "recommendation": "Redirect loop detected. Requires manual correction of target URL."
            }
        
        if idx >= max_redirects:
            return {
                "initial_url": initial_url,
                "status": STATUS_REDIRECT_LOOP,
                "final_url": resp.url,
                "chain": visited_urls,
                "redirect_count": len(visited_urls),
                "recommendation": f"Redirect chain exceeded budget ({max_redirects}). Possible loop."
            }
            
        if resp.status_code == 200:
            if idx == 0:
                return {
                    "initial_url": initial_url,
                    "status": STATUS_OK,
                    "final_url": resp.url,
                    "chain": visited_urls,
                    "redirect_count": 0,
                    "recommendation": "URL is direct and healthy."
                }
            else:
                return {
                    "initial_url": initial_url,
                    "status": STATUS_MOVED,
                    "final_url": resp.url,
                    "chain": visited_urls,
                    "redirect_count": len(visited_urls) - 1,
                    "recommendation": f"Update catalogue entry to final destination: {resp.url}"
                }
        
        # Redirect status codes
        if resp.status_code in (301, 302, 307, 308):
            location = resp.headers.get("Location")
            if location:
                current_url = location
                continue

    return {
        "initial_url": initial_url,
        "status": STATUS_TRANSIENT_ERROR,
        "final_url": visited_urls[-1] if visited_urls else initial_url,
        "chain": visited_urls,
        "redirect_count": len(visited_urls),
        "recommendation": "Unknown or unresolved response. Do not remove link."
    }

def get_fixtures() -> Dict[str, List[MockResponse]]:
    return {
        "fixture_200": [
            MockResponse(200, "https://api.example.com/docs")
        ],
        "fixture_301_to_200": [
            MockResponse(301, "http://api.example.com/docs", {"Location": "https://api.example.com/docs"}),
            MockResponse(200, "https://api.example.com/docs")
        ],
        "fixture_redirect_loop": [
            MockResponse(302, "https://api.example.com/a", {"Location": "https://api.example.com/b"}),
            MockResponse(302, "https://api.example.com/b", {"Location": "https://api.example.com/a"}),
            MockResponse(302, "https://api.example.com/a", {"Location": "https://api.example.com/b"})
        ],
        "fixture_timeout": [
            MockResponse(0, "https://api.example.com/slow", is_timeout=True)
        ],
        "fixture_login_wall": [
            MockResponse(302, "https://api.example.com/dashboard", {"Location": "https://api.example.com/login"}),
            MockResponse(200, "https://api.example.com/login")
        ]
    }

def run_self_test() -> bool:
    print("[*] Running R02-T012 self-test on offline fixtures...")
    fixtures = get_fixtures()
    
    # 1. Test 200 OK
    res_200 = classify_redirect_chain("https://api.example.com/docs", fixtures["fixture_200"])
    assert res_200["status"] == STATUS_OK, f"Expected {STATUS_OK}, got {res_200['status']}"
    assert res_200["redirect_count"] == 0
    print("  [PASS] Offline 200 fixture correctly classified")
    
    # 2. Test 301 -> 200
    res_301 = classify_redirect_chain("http://api.example.com/docs", fixtures["fixture_301_to_200"])
    assert res_301["status"] == STATUS_MOVED, f"Expected {STATUS_MOVED}, got {res_301['status']}"
    assert res_301["final_url"] == "https://api.example.com/docs"
    print("  [PASS] Offline 301->200 fixture correctly classified")
    
    # 3. Test Redirect Loop
    res_loop = classify_redirect_chain("https://api.example.com/a", fixtures["fixture_redirect_loop"])
    assert res_loop["status"] == STATUS_REDIRECT_LOOP, f"Expected {STATUS_REDIRECT_LOOP}, got {res_loop['status']}"
    print("  [PASS] Offline redirect-loop fixture correctly classified")
    
    # 4. Test Timeout
    res_timeout = classify_redirect_chain("https://api.example.com/slow", fixtures["fixture_timeout"])
    assert res_timeout["status"] == STATUS_TIMEOUT, f"Expected {STATUS_TIMEOUT}, got {res_timeout['status']}"
    assert "do not remove" in res_timeout["recommendation"].lower()
    print("  [PASS] Offline timeout fixture correctly classified")
    
    # 5. Test Login Wall
    res_login = classify_redirect_chain("https://api.example.com/dashboard", fixtures["fixture_login_wall"])
    assert res_login["status"] == STATUS_LOGIN_WALL, f"Expected {STATUS_LOGIN_WALL}, got {res_login['status']}"
    print("  [PASS] Offline login-wall fixture correctly classified")
    
    # 6. Verify policy: No link is removed solely because automated request failed
    assert "do not remove" in res_timeout["recommendation"].lower()
    print("  [PASS] Link retention policy enforced on transient failures")

    print("[+] All self-test assertions PASSED successfully!")
    return True

def run_live_check(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    import urllib.request
    import ssl
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    results = []
    obs_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    for entry in entries:
        url = entry["url"]
        print(f"[*] Checking live: {entry['name']} -> {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (coursework-verifier/1.0)"})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                final_url = resp.url
                code = resp.status
                is_redirect = (final_url.rstrip("/") != url.rstrip("/"))
                status = STATUS_MOVED if is_redirect else STATUS_OK
                results.append({
                    "name": entry["name"],
                    "line": entry["line"],
                    "category": entry["category"],
                    "initial_url": url,
                    "final_url": final_url,
                    "status_code": code,
                    "classification": status,
                    "observation_date": obs_date,
                    "recommendation": f"Update URL to {final_url}" if is_redirect else "Entry URL is current and accurate."
                })
        except urllib.error.HTTPError as e:
            results.append({
                "name": entry["name"],
                "line": entry["line"],
                "category": entry["category"],
                "initial_url": url,
                "final_url": e.url if hasattr(e, "url") else url,
                "status_code": e.code,
                "classification": STATUS_LOGIN_WALL if e.code in (401, 403) else STATUS_TRANSIENT_ERROR,
                "observation_date": obs_date,
                "recommendation": f"Observed HTTP {e.code}. Retain entry pending manual check."
            })
        except Exception as e:
            results.append({
                "name": entry["name"],
                "line": entry["line"],
                "category": entry["category"],
                "initial_url": url,
                "final_url": url,
                "status_code": 0,
                "classification": STATUS_TIMEOUT,
                "observation_date": obs_date,
                "recommendation": f"Transient error ({type(e).__name__}). Retain entry."
            })
    return results

def main():
    parser = argparse.ArgumentParser(description="R02-T012 Redirect Verification Tool")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--live", action="store_true", help="Run live check against selected entries")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
        
    if args.live:
        results = run_live_check(SELECTED_ENTRIES)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n=== Live Check Results ===")
            for r in results:
                print(f"L{r['line']} | {r['name']} | {r['classification']}")
                print(f"  Initial: {r['initial_url']}")
                print(f"  Final:   {r['final_url']}")
                print(f"  Observed: {r['observation_date']}")
                print(f"  Decision: {r['recommendation']}\n")
        sys.exit(0)

    # Default action if no flag passed
    print("R02-T012 Redirect Verification Tool")
    print("Run with --self-test to verify offline fixtures, or --live to inspect selected entries.")
    run_self_test()

if __name__ == "__main__":
    main()
