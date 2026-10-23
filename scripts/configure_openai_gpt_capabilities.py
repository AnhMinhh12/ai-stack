#!/usr/bin/env python3
"""Configure Open WebUI's OpenAI-backed image capabilities without printing secrets.

Run inside the Open WebUI container.  The script reuses the API key already
configured for the public OpenAI connection; it never accepts, prints, or
writes a key into this repository.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse


DB_PATH = Path("/app/backend/data/webui.db")
OPENAI_HOST = "api.openai.com"
IMAGE_MODEL = "gpt-image-1.5"


def is_openai_url(value: object) -> bool:
    try:
        return (urlparse(str(value)).hostname or "").lower() == OPENAI_HOST
    except ValueError:
        return False


def fail(message: str) -> None:
    raise SystemExit(f"FAIL CLOSED: {message}")


def load_json(conn: sqlite3.Connection, key: str, default: object) -> object:
    row = conn.execute("select value from config where key=?", (key,)).fetchone()
    if not row or row[0] is None:
        return default
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        fail(f"invalid JSON in {key}")


def upsert(conn: sqlite3.Connection, key: str, value: object) -> None:
    conn.execute(
        "insert into config(key,value,updated_at) values (?,?,unixepoch()) "
        "on conflict(key) do update set value=excluded.value,updated_at=excluded.updated_at",
        (key, json.dumps(value)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the validated configuration")
    args = parser.parse_args()
    if not DB_PATH.is_file():
        fail("Open WebUI database is unavailable")

    conn = sqlite3.connect(DB_PATH)
    urls = load_json(conn, "openai.api_base_urls", [])
    keys = load_json(conn, "openai.api_keys", [])
    if not isinstance(urls, list) or not isinstance(keys, list):
        fail("OpenAI connection configuration must be lists")
    matches = [(url, keys[index]) for index, url in enumerate(urls) if is_openai_url(url) and index < len(keys)]
    if len(matches) != 1:
        fail("exactly one public OpenAI connection is required")
    base_url, api_key = matches[0]
    if not isinstance(api_key, str) or not api_key.strip():
        fail("the public OpenAI connection has no API key")

    changes = {
        "image_generation.enable": True,
        "image_generation.prompt.enable": True,
        "image_generation.engine": "openai",
        "image_generation.model": IMAGE_MODEL,
        "image_generation.size": "1024x1024",
        "image_generation.openai.api_base_url": str(base_url).rstrip("/"),
        "image_generation.openai.api_key": api_key,
        "image_generation.openai.api_version": "",
        "image_generation.openai.params": {},
        "images.edit.enable": True,
        "images.edit.engine": "openai",
        "images.edit.model": IMAGE_MODEL,
        "images.edit.size": "1024x1024",
        "images.edit.openai.api_base_url": str(base_url).rstrip("/"),
        "images.edit.openai.api_key": api_key,
        "images.edit.openai.api_version": "",
    }
    if args.apply:
        for key, value in changes.items():
            upsert(conn, key, value)
        conn.commit()
        print("OpenAI GPT capabilities: applied (image generation and editing enabled)")
    else:
        print("OpenAI GPT capabilities: ready (run with --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
