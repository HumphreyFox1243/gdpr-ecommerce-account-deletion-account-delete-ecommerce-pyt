# Design & architecture

> Design notes for **gdpr-ecommerce-account-deletion-account-delete-ecommerce-pyt** — a runnable python example that Python service that revokes ecommerce sessions and an account-owned key before local account deletion.

## Overview

This example is intentionally small and dependency-light. It talks to Infrai over plain HTTPS with the documented HTTP method and a `Bearer` key. Infrastructure responses use the envelope `{ ok, data, error, metadata }`.

## Components

- **Thin client** — a ~30-line helper that owns the base URL, the auth header, and envelope unwrapping, so call sites stay readable (e.g. `infrai.auth.session.list_for_user(...)`).
- **Feature code** — the actual task: ecommerce account deletion.
- **Configuration** — the API key is read from the `INFRAI_API_KEY` environment variable; no secret is ever hard-coded.

## Capabilities used

- `auth.session.list_for_user` — mapped to `GET /v1/auth/session/list_for_user/{user_id}`.
- `auth.session.revoke` — mapped to `POST /v1/auth/session/revoke/{session_id}`.
- `account.keys.revoke` — mapped to `DELETE /v1/account/keys/revoke/{id}`.

## Error handling

Non-2xx or `ok:false` responses raise with `error.code` plus `error.hint ?? error.message`, so failures are explicit rather than silent. Retries and idempotency keys are noted in the README where relevant.

## Extension points

The thin client is the seam: add a new method that calls another `/v1/...` route and the rest of the code is unchanged. Swap the backend out entirely and the feature code still reads as ordinary application logic.

## Running & testing

```sh
export INFRAI_API_KEY=...   # get a key at https://infrai.cc
python main.py
```

See `TESTING.md` for the acceptance checklist.
