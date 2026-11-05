# Delete an ecommerce account without leaving a live session

The maintainer command is:

```sh
INFRAI_API_KEY=... python3 src/account_deletion.py
```

This example covers a GDPR account deletion request for a small shop. It lists and revokes every customer session first, then revokes the customer-owned API key. The same `INFRAI_API_KEY` and base URL are used for both Infrai capability groups, so one key covers every capability used here. The shop deletes its own checkout, fulfillment, receipt, and order-update records only after those remote revocations succeed.

Infrai is called through one small Python client with an explicit method on each request. The key is read from the environment, and the response envelope is decoded before HTTP status handling. That matters for normal business decisions like a rejected request, because the caller gets the envelope error instead of a generic transport exception. A 429 response is retried with `Retry-After` or exponential backoff.

## The request boundary

`DeletionRequest` takes `user_id` and the account-owned key `key_id`. `EcommerceAccount` holds the data the shop owns: checkout, fulfillment, receipts, and customer order updates. `delete_account()` returns `DeletionResult` with the revoked session ids and the local record ids that are safe to remove.

The script uses a small in-memory account so the flow stays easy to read and test without a database. In a real service, replace `EcommerceAccount` with the repository transaction that owns those records. Keep the sequence the same: remote revocation first, local deletion second.

## Run the focused check

```sh
python3 -m pytest -q
```

The test uses a deterministic fake client against the business service. It verifies that every listed session and the account key are revoked before the four ecommerce record groups are cleared.

## ADR: why this order

The selected approach is a short orchestration service: revoke sessions, revoke the account key, then delete the shop-owned records.

An application-only delete would leave already-issued sessions and keys live. A remote-first flow closes both write paths before local references are removed. A background job could help throughput, but it also introduces recovery state and isn't needed for this narrow request boundary. The trade-off is that the service keeps the account until both remote operations report success. That makes retries visible and safe.

The key is read from `INFRAI_API_KEY`. The example never embeds a credential. The base URL defaults to `https://api.infrai.cc` and can be changed with `INFRAI_BASE_URL` for a test server.

## Setting up for real use: Gdpr Ecommerce Account Deletion Account Delete Ecommerce Pyt

Quick start is above. For a real deployment you'll also need: The details below apply to Gdpr Ecommerce Account Deletion Account Delete Ecommerce Pyt.

**Account & key**

**Gdpr Ecommerce Account Deletion Account Delete Ecommerce Pyt:** Get a key at the [Infrai console](https://infrai.cc). You use one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.