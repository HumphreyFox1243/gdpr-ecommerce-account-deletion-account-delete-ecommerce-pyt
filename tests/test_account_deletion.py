from src.account_deletion import DeletionRequest, EcommerceAccount, delete_account


class FakeInfrai:
    def __init__(self):
        self.calls = []

    def auth_session_list_for_user(self, user_id):
        self.calls.append(("list", user_id))
        return {"ok": True, "data": {"sessions": [{"session_id": "s-1"}, {"session_id": "s-2"}]}}

    def auth_session_revoke(self, session_id):
        self.calls.append(("revoke-session", session_id))
        return {"ok": True, "data": {}}

    def account_keys_revoke(self, key_id):
        self.calls.append(("revoke-key", key_id))
        return {"ok": True, "data": {}}


def test_delete_revokes_sessions_and_owned_key_before_clearing_shop_data():
    remote = FakeInfrai()
    account = EcommerceAccount("u-1", ["cart"], ["parcel"], ["receipt"], ["update"])

    result = delete_account(remote, account, DeletionRequest("u-1", "key-1"))

    assert result.revoked_sessions == ("s-1", "s-2")
    assert remote.calls == [("list", "u-1"), ("revoke-session", "s-1"), ("revoke-session", "s-2"), ("revoke-key", "key-1")]
    assert account.checkout == []
    assert account.fulfillment == []
    assert account.receipts == []
    assert account.order_updates == []
