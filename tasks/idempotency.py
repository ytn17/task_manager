idempotency_store = {}


def check_idempotency(key, body):

    if not key:
        return None, None

    # Check whether this key was previously used
    existing = idempotency_store.get(key)

    if existing is None:
        return None, None

    if existing["body"] != body:
        return "CONFLICT", None

    # Same key and same body
    return "REPLAY", existing["response"]


def store_idempotency(key, body, response):

    if not key:
        return

    idempotency_store[key] = {
        "body": body,
        "response": response
    }
