#!/usr/bin/env python3
"""Load local demo text files into the Onyx ingestion API.

Usage:
    python scripts/load_demo_data.py

Set environment variables before running against a real environment:
    ONYX_BASE_URL=https://your-onyx-host
    ONYX_API_KEY=replace-with-real-api-key
"""

from __future__ import annotations

import json
import os
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error
from urllib import request

DEMO_DATA_DIR = Path(__file__).resolve().parents[1] / "demo-data"
INGESTION_PATH = "/api/onyx-api/ingestion"
DEFAULT_BASE_URL = "http://localhost:3000"
DEFAULT_API_KEY = "REPLACE_WITH_ONYX_API_KEY"


def _build_payload(file_path: Path) -> dict[str, Any]:
    text = file_path.read_text(encoding="utf-8").strip()
    semantic_identifier = file_path.stem.replace("_", " ").title()

    return {
        "document": {
            "semantic_identifier": semantic_identifier,
            "source": "file",
            "metadata": {
                "dataset": "dealpilot-demo",
                "file_name": file_path.name,
                "document_type": "sales_demo_data",
                "uploaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            },
            "sections": [
                {
                    "text": text,
                    "link": f"demo-data/{file_path.name}",
                }
            ],
        }
    }


def _post_document(base_url: str, api_key: str, payload: dict[str, Any]) -> None:
    url = f"{base_url.rstrip('/')}{INGESTION_PATH}"
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    req = request.Request(url, data=data, headers=headers, method="POST")

    with request.urlopen(req, timeout=30) as response:  # noqa: S310
        body = response.read().decode("utf-8")
        print(f"Indexed: {payload['document']['semantic_identifier']} -> {body}")


def main() -> None:
    base_url = os.getenv("ONYX_BASE_URL", DEFAULT_BASE_URL)
    api_key = os.getenv("ONYX_API_KEY", DEFAULT_API_KEY)

    if api_key == DEFAULT_API_KEY:
        print(
            "Warning: ONYX_API_KEY is not set. Update the placeholder key before running against a real Onyx instance."
        )

    if not DEMO_DATA_DIR.exists():
        raise FileNotFoundError(f"Demo data folder not found: {DEMO_DATA_DIR}")

    files = sorted(DEMO_DATA_DIR.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No .txt files found in {DEMO_DATA_DIR}")

    print(f"Loading {len(files)} demo files from {DEMO_DATA_DIR} to {base_url}{INGESTION_PATH}")

    for file_path in files:
        payload = _build_payload(file_path)
        try:
            _post_document(base_url=base_url, api_key=api_key, payload=payload)
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            print(f"HTTP error for {file_path.name}: {exc.code} {details}")
        except error.URLError as exc:
            print(f"Connection error for {file_path.name}: {exc.reason}")


if __name__ == "__main__":
    main()
