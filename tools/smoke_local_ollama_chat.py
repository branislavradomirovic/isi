from __future__ import annotations

import argparse
import sys
from typing import Any

import httpx


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def scope_items(context: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for org in context.get("organizations", []):
        for product in org.get("products", []):
            workspaces = product.get("workspaces", [])
            if workspaces:
                result[product["code"]] = {
                    "organization_id": str(org["id"]),
                    "product_code": str(product["code"]),
                    "workspace_id": str(workspaces[0]["id"]),
                }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8004")
    parser.add_argument("--ollama-base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="qwen2.5:7b-instruct")
    parser.add_argument("--email", default="isi05-dual@example.com")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    try:
        tags = httpx.get(f"{args.ollama_base_url.rstrip('/')}/api/tags", timeout=5)
        tags.raise_for_status()
    except httpx.HTTPError as exc:
        return fail(f"local Ollama unavailable: {exc}")
    names = {
        str(value)
        for item in tags.json().get("models", [])
        for value in (item.get("name"), item.get("model"))
        if value
    }
    if args.model not in names:
        return fail(f"required Ollama model is not installed: {args.model}; installed={sorted(names)}")
    print(f"PASS Ollama preflight -> {args.model}")

    base = args.base_url.rstrip("/")
    login = httpx.post(
        f"{base}/api/v1/auth/login",
        json={"email": args.email, "password": args.password},
        timeout=10,
    )
    if login.status_code != 200:
        return fail(f"login -> {login.status_code} {login.text}")
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    context = httpx.get(f"{base}/api/v1/app-context", headers=headers, timeout=10)
    if context.status_code != 200:
        return fail(f"app-context -> {context.status_code} {context.text}")
    scopes = scope_items(context.json())
    scope = scopes.get("ORDO") or scopes.get("SIMPA")
    if scope is None:
        return fail("no QA workspace available for real Ollama smoke")

    models = httpx.get(f"{base}/api/v1/ai/models", headers=headers, params=scope, timeout=10)
    if models.status_code != 200:
        return fail(f"AI models -> {models.status_code} {models.text}")
    model = next((item for item in models.json() if item.get("model_key") == "isi-ollama-chat-default"), None)
    if model is None:
        return fail("isi-ollama-chat-default is not registered")
    if model.get("provider_type") != "ollama" or model.get("model_name") != args.model:
        return fail(f"Ollama registry mismatch -> {model}")

    payload = {
        **scope,
        "input_text": "Return the requested infrastructure diagnostic JSON only.",
        "prompt_key": "foundation.diagnostic",
        "model_key": "isi-ollama-chat-default",
        "sensitivity": "internal",
    }
    response = httpx.post(f"{base}/api/v1/ai/jobs", headers=headers, json=payload, timeout=180)
    if response.status_code != 202:
        return fail(f"real Ollama AI job -> {response.status_code} {response.text}")
    job = response.json()
    if job.get("status") != "succeeded":
        return fail(f"real Ollama job status -> {job.get('status')} error={job.get('error_code')} {job.get('error_message')}")
    if job.get("provider_name") != "ollama":
        return fail(f"real Ollama job fell back to {job.get('provider_name')}")
    if job.get("model_name") != args.model:
        return fail(f"real Ollama model mismatch -> {job.get('model_name')}")
    structured = job.get("structured_output") or {}
    if structured.get("status") != "ok" or not isinstance(structured.get("message"), str):
        return fail(f"real Ollama structured output invalid -> {structured}")
    print(
        f"PASS real ISI Ollama gateway -> product={scope['product_code']} provider={job['provider_name']} "
        f"model={job['model_name']} latency_ms={job.get('latency_ms')}"
    )
    httpx.post(f"{base}/api/v1/auth/logout", headers=headers, timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
