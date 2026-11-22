#!/usr/bin/env python3
"""
R02-T017: HTTP failure classification for Public APIs catalogue.
Category: Shopping [README.md]
Task: R02-T017 · 7 of 10

Selected entries:
- ARC: https://www.arcreport.ai/developers (Line 2249)
- Best Buy: https://bestbuyapis.github.io/api-documentation/#overview (Line 2250)
- BirkinBagStock: https://birkinbagstock.com/.well-known/openapi.json (Line 2251)
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, Optional

LABEL_SUCCESS = "SUCCESS_200"
LABEL_NOT_FOUND = "MISSING_RESOURCE_404"
LABEL_RATE_LIMIT = "RATE_LIMITED_429"
LABEL_FORBIDDEN = "FORBIDDEN_403"
LABEL_FALLBACK_OK = "HEAD_405_GET_200_SUCCESS"
LABEL_TIMEOUT = "REQUEST_TIMEOUT"
LABEL_DNS_FAILURE = "DNS_RESOLUTION_FAILURE"

SELECTED_ENTRIES = [
    {
        "name": "ARC",
        "url": "https://www.arcreport.ai/developers",
        "line": 2249,
        "category": "Shopping"
    },
    {
        "name": "Best Buy",
        "url": "https://bestbuyapis.github.io/api-documentation/#overview",
        "line": 2250,
        "category": "Shopping"
    },
    {
        "name": "BirkinBagStock",
        "url": "https://birkinbagstock.com/.well-known/openapi.json",
        "line": 2251,
        "category": "Shopping"
    }
]

def classify_probe(head_status: Optional[int], get_status: Optional[int], is_timeout: bool = False, is_dns_error: bool = False) -> Dict[str, Any]:
    """
    Classifies HTTP probe response distinguishing success, missing resources,
    rate limits, timeouts, DNS errors, and HEAD->GET fallbacks.
    """
    if is_dns_error:
        return {
            "label": LABEL_DNS_FAILURE,
            "status_code": 0,
            "can_remove": False,
            "recommendation": "DNS resolution failure. Retain link; do not remove without manual DNS verification."
        }
    if is_timeout:
        return {
            "label": LABEL_TIMEOUT,
            "status_code": 0,
            "can_remove": False,
            "recommendation": "Request timed out. Retain link; transient failure."
        }
    
    # Check HEAD fallback
    if head_status == 405 and get_status == 200:
        return {
            "label": LABEL_FALLBACK_OK,
            "status_code": 200,
            "can_remove": False,
            "recommendation": "HEAD unsupported (405); fallback GET succeeded (200). Resource is healthy."
        }
        
    code = get_status if get_status is not None else head_status
    if code == 200:
        return {
            "label": LABEL_SUCCESS,
            "status_code": 200,
            "can_remove": False,
            "recommendation": "Resource available and healthy."
        }
    elif code == 404:
        return {
            "label": LABEL_NOT_FOUND,
            "status_code": 404,
            "can_remove": True,
            "recommendation": "Missing resource (404 Not Found). Recommended for catalogue removal only after manual confirmation."
        }
    elif code == 429:
        return {
            "label": LABEL_RATE_LIMIT,
            "status_code": 429,
            "can_remove": False,
            "recommendation": "Rate limited (429 Too Many Requests). Retain link."
        }
    elif code == 403:
        return {
            "label": LABEL_FORBIDDEN,
            "status_code": 403,
            "can_remove": False,
            "recommendation": "Forbidden (403 / Cloudflare / WAF). Retain link; service is active."
        }
    
    return {
        "label": f"HTTP_{code}",
        "status_code": code,
        "can_remove": False,
        "recommendation": f"Received HTTP {code}. Retain link."
    }

def get_fixtures() -> Dict[str, Dict[str, Any]]:
    return {
        "case_200": {"head_status": 200, "get_status": 200, "is_timeout": False, "is_dns_error": False},
        "case_404": {"head_status": 404, "get_status": 404, "is_timeout": False, "is_dns_error": False},
        "case_429": {"head_status": 429, "get_status": 429, "is_timeout": False, "is_dns_error": False},
        "case_head405_get200": {"head_status": 405, "get_status": 200, "is_timeout": False, "is_dns_error": False},
        "case_timeout": {"head_status": None, "get_status": None, "is_timeout": True, "is_dns_error": False},
        "case_dns_error": {"head_status": None, "get_status": None, "is_timeout": False, "is_dns_error": True}
    }

def run_self_test() -> bool:
    print("[*] Running R02-T017 self-test on HTTP status classification fixtures...")
    fixtures = get_fixtures()

    # 1. 200 Success
    res_200 = classify_probe(**fixtures["case_200"])
    assert res_200["label"] == LABEL_SUCCESS
    assert res_200["can_remove"] is False
    print("  [PASS] 200 Success fixture correctly labeled")

    # 2. 404 Missing Resource
    res_404 = classify_probe(**fixtures["case_404"])
    assert res_404["label"] == LABEL_NOT_FOUND
    assert res_404["can_remove"] is True
    assert "manual confirmation" in res_404["recommendation"].lower()
    print("  [PASS] 404 Missing Resource correctly labeled and flagged for manual removal confirmation")

    # 3. 429 Rate Limit
    res_429 = classify_probe(**fixtures["case_429"])
    assert res_429["label"] == LABEL_RATE_LIMIT
    assert res_429["can_remove"] is False
    print("  [PASS] 429 Rate Limited correctly labeled and retained")

    # 4. HEAD 405 -> GET 200 fallback
    res_fb = classify_probe(**fixtures["case_head405_get200"])
    assert res_fb["label"] == LABEL_FALLBACK_OK
    assert res_fb["can_remove"] is False
    print("  [PASS] HEAD-405/GET-200 fallback correctly identified and retained")

    # 5. Timeout
    res_to = classify_probe(**fixtures["case_timeout"])
    assert res_to["label"] == LABEL_TIMEOUT
    assert res_to["can_remove"] is False
    print("  [PASS] Timeout correctly labeled as transient failure and retained")

    # 6. DNS failure
    res_dns = classify_probe(**fixtures["case_dns_error"])
    assert res_dns["label"] == LABEL_DNS_FAILURE
    assert res_dns["can_remove"] is False
    print("  [PASS] DNS error correctly labeled and retained")

    # 7. Verify all labels are distinct
    labels = {res_200["label"], res_404["label"], res_429["label"], res_fb["label"], res_to["label"], res_dns["label"]}
    assert len(labels) == 6, "Expected 6 distinct classification labels!"
    print("  [PASS] All 6 conditions produce completely distinct labels")

    # 8. Policy verification: Only manually confirmed 404 can be proposed for removal
    for label_name, r in [("200", res_200), ("429", res_429), ("fallback", res_fb), ("timeout", res_to), ("dns", res_dns)]:
        assert r["can_remove"] is False, f"Rule violation: {label_name} should never be marked for removal"
    print("  [PASS] Strict retention policy enforced across all non-404 conditions")

    print("[+] All R02-T017 self-test assertions PASSED successfully!")
    return True

def run_live():
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("\n=== Live Probing Selected Shopping Entries ===")
    for entry in SELECTED_ENTRIES:
        url = entry["url"]
        head_status, get_status = None, None
        is_to, is_dns = False, False
        
        # Probe with HEAD first
        head_req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
        try:
            with urllib.request.urlopen(head_req, context=ctx, timeout=5) as r:
                head_status = r.status
        except urllib.error.HTTPError as e:
            head_status = e.code
        except Exception:
            head_status = None

        # If head failed or was not 200, try GET
        if head_status != 200:
            get_req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="GET")
            try:
                with urllib.request.urlopen(get_req, context=ctx, timeout=5) as r:
                    get_status = r.status
            except urllib.error.HTTPError as e:
                get_status = e.code
            except Exception as e:
                if "timed out" in str(e).lower():
                    is_to = True
                elif "nodename" in str(e).lower() or "servname" in str(e).lower():
                    is_dns = True

        classification = classify_probe(head_status, get_status, is_to, is_dns)
        print(f"L{entry['line']} | {entry['name']}: {url}")
        print(f"  HEAD: {head_status} | GET: {get_status} -> {classification['label']}")
        print(f"  Action: {classification['recommendation']}\n")

def main():
    parser = argparse.ArgumentParser(description="R02-T017 Failure Classifier Tool")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--live", action="store_true", help="Run live HTTP probes with GET fallback")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
        
    if args.live:
        run_live()
        sys.exit(0)

    run_self_test()

if __name__ == "__main__":
    main()
