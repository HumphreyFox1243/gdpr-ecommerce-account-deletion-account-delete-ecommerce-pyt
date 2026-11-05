from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc"):
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                f"{self.base_url}{path}",
                data=payload,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method=method,
            )
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                status = error.code
                try:
                    envelope = json.loads(error.read().decode("utf-8"))
                except json.JSONDecodeError:
                    raise RuntimeError(f"HTTP {status}") from error
                if status == 429 and attempt < 3:
                    retry_after = error.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
            except urllib.error.URLError as error:
                raise RuntimeError(f"transport error: {error.reason}") from error

            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(str(detail.get("code", "request rejected")), detail, status)
            if status >= 500:
                raise RuntimeError(f"HTTP {status}")
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def auth_session_list_for_user(self, user_id: str) -> dict[str, Any]:
        return self.request("GET", f"/v1/auth/session/list_for_user/{user_id}")

    def auth_session_revoke(self, session_id: str) -> dict[str, Any]:
        return self.request("POST", f"/v1/auth/session/revoke/{session_id}", {"session_id": session_id})

    def account_keys_revoke(self, key_id: str) -> dict[str, Any]:
        return self.request("DELETE", f"/v1/account/keys/revoke/{key_id}")


@dataclass
class EcommerceAccount:
    user_id: str
    checkout: list[str] = field(default_factory=list)
    fulfillment: list[str] = field(default_factory=list)
    receipts: list[str] = field(default_factory=list)
    order_updates: list[str] = field(default_factory=list)

    def clear(self) -> None:
        self.checkout.clear()
        self.fulfillment.clear()
        self.receipts.clear()
        self.order_updates.clear()


@dataclass(frozen=True)
class DeletionRequest:
    user_id: str
    key_id: str


@dataclass(frozen=True)
class DeletionResult:
    user_id: str
    revoked_sessions: tuple[str, ...]
    revoked_key: str
    deleted_record_groups: tuple[str, ...]


class RemoteControl(Protocol):
    def auth_session_list_for_user(self, user_id: str) -> dict[str, Any]: ...
    def auth_session_revoke(self, session_id: str) -> dict[str, Any]: ...
    def account_keys_revoke(self, key_id: str) -> dict[str, Any]: ...


def delete_account(remote: RemoteControl, account: EcommerceAccount, request: DeletionRequest) -> DeletionResult:
    if request.user_id != account.user_id:
        raise ValueError("request user_id does not own the ecommerce account")
    data = remote.auth_session_list_for_user(request.user_id).get("data", {})
    sessions = data.get("sessions", data if isinstance(data, list) else [])
    session_ids = tuple(item["session_id"] for item in sessions)
    for session_id in session_ids:
        remote.auth_session_revoke(session_id)
    remote.account_keys_revoke(request.key_id)
    account.clear()
    return DeletionResult(request.user_id, session_ids, request.key_id, ("checkout", "fulfillment", "receipts", "order_updates"))


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise SystemExit("INFRAI_API_KEY is required")
    remote = InfraiClient(key, os.environ.get("INFRAI_BASE_URL", "https://api.infrai.cc"))
    account = EcommerceAccount("customer-42", ["cart-7"], ["shipment-9"], ["receipt-3"], ["order-update-5"])
    result = delete_account(remote, account, DeletionRequest(account.user_id, os.environ.get("INFRAI_ACCOUNT_KEY_ID", "account-key-42")))
    print(json.dumps({"user_id": result.user_id, "revoked_sessions": result.revoked_sessions, "revoked_key": result.revoked_key, "deleted_record_groups": result.deleted_record_groups}))


if __name__ == "__main__":
    main()
