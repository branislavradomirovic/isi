from __future__ import annotations

import argparse
import sys
from typing import Any

import httpx


def fail(label: str, response: httpx.Response) -> int:
    print(f"FAIL {label}: {response.status_code} {response.text}")
    return 1


def scope_items(context: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for org in context.get("organizations", []):
        for product in org.get("products", []):
            workspaces = product.get("workspaces", [])
            if not workspaces:
                continue
            result[product["code"]] = {
                "organization_id": str(org["id"]),
                "product_code": product["code"],
                "workspace_id": str(workspaces[0]["id"]),
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8004")
    parser.add_argument("--email", default="isi05-dual@example.com")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    login = httpx.post(f"{base}/api/v1/auth/login", json={"email": args.email, "password": args.password}, timeout=10)
    if login.status_code != 200:
        return fail("login", login)
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    context_response = httpx.get(f"{base}/api/v1/app-context", headers=headers, timeout=10)
    if context_response.status_code != 200:
        return fail("app-context", context_response)
    scopes = scope_items(context_response.json())
    if "SIMPA" not in scopes or "ORDO" not in scopes:
        print("FAIL dual QA user must expose SIMPA and ORDO workspaces")
        return 1

    created: dict[str, dict[str, Any]] = {}
    for product_code in ("SIMPA", "ORDO"):
        params = scopes[product_code]
        capability = httpx.get(f"{base}/api/v1/ai/capabilities", headers=headers, params=params, timeout=10)
        if capability.status_code != 200:
            return fail(f"{product_code} capabilities", capability)
        models = httpx.get(f"{base}/api/v1/ai/models", headers=headers, params=params, timeout=10)
        if models.status_code != 200:
            return fail(f"{product_code} models", models)
        prompts = httpx.get(f"{base}/api/v1/ai/prompts", headers=headers, params=params, timeout=10)
        if prompts.status_code != 200:
            return fail(f"{product_code} prompts", prompts)
        chat_stub = next((item for item in models.json() if item["model_key"] == "isi-dev-stub-chat"), None)
        embed_stub = next((item for item in models.json() if item["model_key"] == "isi-dev-stub-embedding"), None)
        if chat_stub is None or embed_stub is None:
            print(f"FAIL {product_code}: development stub models are missing")
            return 1
        sensitivity = "sensitive" if product_code == "SIMPA" else "internal"
        payload = {
            **params,
            "input_text": f"QA infrastructure diagnostic for {product_code}",
            "prompt_key": "foundation.diagnostic",
            "model_key": chat_stub["model_key"],
            "sensitivity": sensitivity,
        }
        job = httpx.post(f"{base}/api/v1/ai/jobs", headers=headers, json=payload, timeout=20)
        if job.status_code != 202:
            return fail(f"{product_code} AI job", job)
        data = job.json()
        expected_status = "review_required" if product_code == "SIMPA" else "succeeded"
        if data["status"] != expected_status:
            print(f"FAIL {product_code} status: expected {expected_status}, got {data['status']}")
            return 1
        if data["effective_provider_policy"] != "local_only":
            print(f"FAIL {product_code} policy is not local_only")
            return 1
        if data["provider_name"] != "development-stub":
            print(f"FAIL {product_code} did not execute through QA stub")
            return 1
        created[product_code] = data

        namespace = f"ORG-{params['organization_id']}/{product_code}"
        embedding = httpx.post(
            f"{base}/api/v1/ai/embeddings",
            headers=headers,
            json={
                **params,
                "namespace": namespace,
                "source_type": "qa",
                "source_id": f"isi07-{product_code.lower()}",
                "chunk_index": 0,
                "text": f"Embedding QA for {product_code}",
                "model_key": embed_stub["model_key"],
                "sensitivity": sensitivity,
            },
            timeout=20,
        )
        if embedding.status_code != 201:
            return fail(f"{product_code} embedding", embedding)
        if embedding.json()["dimensions"] != 16:
            print(f"FAIL {product_code} development embedding dimensions")
            return 1
        print(
            f"PASS {product_code}: job={data['status']} policy={data['effective_provider_policy']} "
            f"provider={data['provider_name']} pgvector={capability.json()['pgvector_enabled']}"
        )

    simpa_job = created["SIMPA"]
    ordo_scope = scopes["ORDO"]
    cross = httpx.get(
        f"{base}/api/v1/ai/jobs/{simpa_job['id']}",
        headers=headers,
        params=ordo_scope,
        timeout=10,
    )
    if cross.status_code not in {403, 404}:
        print(f"FAIL cross-product AI job lookup returned {cross.status_code}")
        return 1
    print(f"PASS cross-product private job isolation -> {cross.status_code}")

    invalid_namespace = httpx.post(
        f"{base}/api/v1/ai/embeddings",
        headers=headers,
        json={
            **ordo_scope,
            "namespace": f"ORG-{ordo_scope['organization_id']}/SIMPA",
            "source_type": "qa",
            "source_id": "cross-product-negative-control",
            "chunk_index": 0,
            "text": "must be rejected",
            "model_key": "isi-dev-stub-embedding",
            "sensitivity": "internal",
        },
        timeout=20,
    )
    if invalid_namespace.status_code != 400:
        print(f"FAIL cross-product namespace negative control -> {invalid_namespace.status_code}")
        return 1
    print("PASS cross-product RAG namespace negative control -> 400")

    try:
        tags = httpx.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
        if tags.status_code == 200:
            model_names = [item.get("name", "") for item in tags.json().get("models", [])]
            print(f"Ollama optional capability: AVAILABLE ({len(model_names)} model(s))")
        else:
            print(f"Ollama optional capability: HTTP {tags.status_code}; QA stub remains authoritative for this gate")
    except httpx.HTTPError:
        print("Ollama optional capability: unavailable; QA stub remains authoritative for this gate")

    httpx.post(f"{base}/api/v1/auth/logout", headers=headers, timeout=10)
    print("ISI-07 shared AI API smoke PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
