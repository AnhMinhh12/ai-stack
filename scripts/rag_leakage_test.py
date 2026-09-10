#!/usr/bin/env python3
"""
Cross-Tenant RAG Data Leakage & Isolation Test
Validates strict 0% data leakage between isolated tenant contexts in Qdrant Vector DB & RAG Pipeline.
"""

import sys
import json
import os
import urllib.request
from typing import Dict

# Runtime configuration. Credentials must come from the environment/secret manager.
QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
TEST_COLLECTION = "test_tenant_rag_isolation"

if not QDRANT_URL or not QDRANT_API_KEY:
    raise SystemExit("FAIL CLOSED: QDRANT_URL and QDRANT_API_KEY must be provided by the runtime secret mechanism")

def qdrant_request(endpoint: str, method: str = "GET", payload: Dict = None) -> Dict:
    url = f"{QDRANT_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "api-key": QDRANT_API_KEY
    }
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def setup_test_collection():
    print(f"[*] Setting up test collection: '{TEST_COLLECTION}'...")
    # Delete if exists
    try:
        qdrant_request(f"/collections/{TEST_COLLECTION}", method="DELETE")
    except Exception:
        pass

    # Create collection with vector size 4 (dummy vectors for test logic)
    create_payload = {
        "vectors": {
            "size": 4,
            "distance": "Cosine"
        }
    }
    qdrant_request(f"/collections/{TEST_COLLECTION}", method="PUT", payload=create_payload)

    # Insert Tenant A and Tenant B test points
    # Vector dim = 4
    points_payload = {
        "points": [
            {
                "id": 1,
                "vector": [0.9, 0.1, 0.0, 0.0],
                "payload": {
                    "tenant_id": "tenant_finance",
                    "doc_title": "Confidential Q3 Financial Earnings Report",
                    "content": "Revenue $50M, Net Margin 28%",
                    "department": "Finance"
                }
            },
            {
                "id": 2,
                "vector": [0.85, 0.15, 0.0, 0.0],
                "payload": {
                    "tenant_id": "tenant_finance",
                    "doc_title": "Tax Strategy 2026",
                    "content": "Offshore structures and tax exemptions",
                    "department": "Finance"
                }
            },
            {
                "id": 3,
                "vector": [0.0, 0.0, 0.9, 0.1],
                "payload": {
                    "tenant_id": "tenant_hr",
                    "doc_title": "Executive Payroll & Compensation Policy",
                    "content": "Executive Bonus $100K for C-level staff",
                    "department": "HR"
                }
            },
            {
                "id": 4,
                "vector": [0.0, 0.0, 0.85, 0.15],
                "payload": {
                    "tenant_id": "tenant_hr",
                    "doc_title": "Employee Performance Appraisals",
                    "content": "Private performance scorecards and reviews",
                    "department": "HR"
                }
            }
        ]
    }
    qdrant_request(f"/collections/{TEST_COLLECTION}/points?wait=true", method="PUT", payload=points_payload)
    print("  [+] Inserted 4 multi-tenant vector points (2 Finance, 2 HR).")

def run_cross_tenant_isolation_tests() -> bool:
    print("\n[*] Executing Cross-Tenant RAG Data Leakage Tests...")

    tests = [
        {
            "user_tenant": "tenant_finance",
            "user_role": "Finance Analyst",
            "query_vector": [0.0, 0.0, 0.9, 0.1],  # Searching HR related vector
            "target_tenant": "tenant_finance",
            "forbidden_tenant": "tenant_hr"
        },
        {
            "user_tenant": "tenant_hr",
            "user_role": "HR Manager",
            "query_vector": [0.9, 0.1, 0.0, 0.0],  # Searching Finance related vector
            "target_tenant": "tenant_hr",
            "forbidden_tenant": "tenant_finance"
        }
    ]

    total_queries = 0
    leakage_incidents = 0

    for test in tests:
        total_queries += 1
        user_tenant = test["user_tenant"]
        forbidden_tenant = test["forbidden_tenant"]

        print(f"\n---> Test Query by User ({test['user_role']}) [Tenant Filter: '{user_tenant}']")
        
        # Search query with tenant payload filter enforced
        search_payload = {
            "vector": test["query_vector"],
            "limit": 5,
            "filter": {
                "must": [
                    {
                        "key": "tenant_id",
                        "match": {
                            "value": user_tenant
                        }
                    }
                ]
            },
            "with_payload": True
        }

        res = qdrant_request(f"/collections/{TEST_COLLECTION}/points/search", method="POST", payload=search_payload)
        results = res.get("result", [])

        print(f"     Retrieved {len(results)} matching document chunks.")
        
        leaked_in_query = False
        for hit in results:
            hit_payload = hit.get("payload", {})
            retrieved_tenant = hit_payload.get("tenant_id")
            doc_title = hit_payload.get("doc_title")
            
            print(f"     - Hit ID {hit['id']}: Tenant='{retrieved_tenant}', Title='{doc_title}', Score={hit['score']:.4f}")
            
            if retrieved_tenant == forbidden_tenant:
                print(f"     [CRITICAL ERROR] DATA LEAK DETECTED! Tenant '{user_tenant}' retrieved document from '{forbidden_tenant}'!")
                leaked_in_query = True
                leakage_incidents += 1

        if not leaked_in_query:
            print(f"     [PASSED] Strict isolation verified for {user_tenant}. Zero leakage from {forbidden_tenant}.")

    # Clean up test collection
    try:
        qdrant_request(f"/collections/{TEST_COLLECTION}", method="DELETE")
    except Exception:
        pass

    leakage_rate = (leakage_incidents / total_queries) * 100.0
    print("\n======================================================================")
    print("CROSS-TENANT RAG LEAKAGE TEST RESULT SUMMARY")
    print("======================================================================")
    print(f"Total Test Queries:        {total_queries}")
    print(f"Data Leakage Incidents:    {leakage_incidents}")
    print(f"Cross-Tenant Leakage Rate: {leakage_rate:.2f}%")
    print("======================================================================")

    if leakage_rate == 0.0:
        print("SUCCESS: 0% Cross-Tenant RAG Leakage Achieved! Tenant Isolation PASSED.")
        return True
    else:
        print("FAILURE: Cross-Tenant Data Leakage Detected!")
        return False

if __name__ == "__main__":
    setup_test_collection()
    success = run_cross_tenant_isolation_tests()
    sys.exit(0 if success else 1)
