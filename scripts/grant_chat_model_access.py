#!/usr/bin/env python3
"""Give the two standard WebUI accounts access to the approved chat models."""

from __future__ import annotations

import argparse
import sqlite3
import time
import uuid


OWNER_EMAIL = "hoanhminhz@gmail.com"
USER_EMAILS = ("products@htmp.com.vn", "sales@htmp.com.vn")
PICKER_MODELS = ("htmp-nhanh", "htmp-erp-agent-staging", "gpt-5.6-sol", "gpt-5.6-luna")
BASE_MODELS = ("qwen2.5-14b",)
MODEL_IDS = PICKER_MODELS + BASE_MODELS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/app/backend/data/webui.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with sqlite3.connect(args.db, timeout=15) as db:
        db.execute("BEGIN IMMEDIATE" if args.apply else "BEGIN")
        users = {
            email: (user_id, role)
            for user_id, email, role in db.execute(
                "SELECT id,email,role FROM user WHERE email IN (?,?,?)",
                (OWNER_EMAIL, *USER_EMAILS),
            )
        }
        if set(users) != {OWNER_EMAIL, *USER_EMAILS}:
            raise SystemExit("Required Open WebUI accounts are missing")
        if users[OWNER_EMAIL][1] != "admin" or any(users[email][1] != "user" for email in USER_EMAILS):
            raise SystemExit("Unexpected account roles; no changes made")

        models = {
            model_id: (owner_id, base_id, active)
            for model_id, owner_id, base_id, active in db.execute(
                "SELECT id,user_id,base_model_id,is_active FROM model WHERE id IN (?,?,?,?,?)",
                MODEL_IDS,
            )
        }
        for model_id in ("htmp-nhanh", "htmp-erp-agent-staging", *BASE_MODELS):
            if model_id not in models or not models[model_id][2]:
                raise SystemExit(f"Required active model is missing: {model_id}")
        for model_id in ("gpt-5.6-sol", "gpt-5.6-luna"):
            if model_id in models and not models[model_id][2]:
                raise SystemExit(f"Approved model is inactive: {model_id}")

        missing_models = [model_id for model_id in PICKER_MODELS if model_id not in models]
        existing_grants = {
            (resource_id, principal_id)
            for resource_id, principal_id in db.execute(
                "SELECT resource_id,principal_id FROM access_grant "
                "WHERE resource_type='model' AND permission='read' "
                "AND principal_type='user' AND resource_id IN (?,?,?,?,?)",
                MODEL_IDS,
            )
        }
        missing_grants = [
            (model_id, users[email][0])
            for email in USER_EMAILS
            for model_id in MODEL_IDS
            if (model_id, users[email][0]) not in existing_grants
        ]
        print(f"Missing model registrations: {', '.join(missing_models) or 'none'}")
        print(f"Missing per-user read grants: {len(missing_grants)}")
        if not args.apply:
            db.rollback()
            return

        now = int(time.time())
        for model_id in missing_models:
            db.execute(
                "INSERT INTO model "
                "(id,user_id,base_model_id,name,params,meta,updated_at,created_at,is_active) "
                "VALUES (?,?,NULL,?,'{}','{}',?,?,1)",
                (model_id, users[OWNER_EMAIL][0], model_id, now, now),
            )
        for model_id, user_id in missing_grants:
            db.execute(
                "INSERT INTO access_grant "
                "(id,resource_type,resource_id,principal_type,principal_id,permission,created_at) "
                "VALUES (?,'model',?,'user',?,'read',?)",
                (str(uuid.uuid4()), model_id, user_id, now),
            )
        db.commit()
        print("Model access updated")


if __name__ == "__main__":
    main()
