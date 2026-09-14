"""The one model interface: generate(prompt, schema, stage) -> dict, priced and logged.

The ingestor's block 2, trimmed: raw HTTP to chat completions, JSON replies, one retry when a
reply does not fit its shape, three retries on a timeout, a 429 or a 5xx. Every call is appended
to a calls log beside the store with its model, tier, tokens, seconds and cost. The key comes
from the OPENAI_API_KEY environment variable and nowhere else.
"""
import http.client
import json
import os
import time
import urllib.error
import urllib.request

LUNA = "gpt-5.6-luna"
TERRA = "gpt-5.6-terra"
SERVICE_TIER = "flex"
PRICE = {"flex": {LUNA: (0.10, 0.60), TERRA: (1.00, 6.00)},
         "default": {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00)}}
KEY = os.environ.get("OPENAI_API_KEY")
LOG_PATH = None
SPENT = 0.0
SPEND_STOP = float(os.environ.get("SPEND_STOP", "10"))


class SchemaError(Exception):
    pass


class SpendStop(Exception):
    pass


def check_schema(reply, schema):
    """`schema` maps a required key to a type (or a tuple of types); extra keys are allowed."""
    if not isinstance(reply, dict):
        raise SchemaError("reply is not an object")
    for key, kind in schema.items():
        if key not in reply:
            raise SchemaError(f"missing {key}")
        if kind is not None and not isinstance(reply[key], kind):
            raise SchemaError(f"{key} is not {kind}")


def log_call(row):
    global SPENT
    SPENT += row.get("cost", 0.0)
    if LOG_PATH:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return resp.status, resp.read().decode("utf-8")


def call(payload, model, stage, ctx, prompt_chars):
    if not KEY:
        raise RuntimeError("no OPENAI_API_KEY in the environment")
    if SPENT >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${SPENT:.2f} of ${SPEND_STOP:.2f}")
    price_in, price_out = PRICE[SERVICE_TIER][model]
    started = time.time()
    for attempt in range(3):
        try:
            status, text = post("https://api.openai.com/v1/chat/completions", payload)
        except urllib.error.HTTPError as error:
            status, text = error.code, error.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            log_call({"stage": stage, "model": model, "in": prompt_chars // 4, "out": 0,
                      "seconds": round(time.time() - started, 1),
                      "cost": prompt_chars // 4 * price_in / 1e6, "timeout": True, **ctx})
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))
            continue
        if status == 429 and "insufficient_quota" in text:
            raise SpendStop(f"OpenAI quota exhausted: {text[:200]}")
        if status == 429 or status >= 500:
            if attempt == 2:
                raise RuntimeError(f"OpenAI {status}: {text}")
            time.sleep(15 * (attempt + 1))
            continue
        if status != 200:
            raise RuntimeError(f"OpenAI {status}: {text}")
        break
    body = json.loads(text)
    tier = body.get("service_tier") or SERVICE_TIER
    price_in, price_out = PRICE.get(tier, PRICE["default"])[model]
    usage = body.get("usage", {})
    tokens_in, tokens_out = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    log_call({"stage": stage, "model": body.get("model", model), "tier": tier, "in": tokens_in,
              "out": tokens_out, "seconds": round(time.time() - started, 1),
              "cost": (tokens_in * price_in + tokens_out * price_out) / 1e6, **ctx})
    return body


def generate(prompt, schema, stage, model=LUNA, effort="low", ctx=None):
    """The reply as a dict that fits `schema`, or None after one retry with the error appended."""
    ctx = ctx or {}
    for attempt in range(2):
        body = call({"model": model, "reasoning_effort": effort, "service_tier": SERVICE_TIER,
                     "response_format": {"type": "json_object"},
                     "messages": [{"role": "user", "content": prompt}]},
                    model, stage, ctx, len(prompt))
        try:
            message = body["choices"][0]["message"]
            if not message.get("content"):
                raise SchemaError("empty reply")
            reply = json.loads(message["content"])
            check_schema(reply, schema)
            return reply
        except (SchemaError, ValueError, TypeError, KeyError, IndexError) as e:
            log_call({"stage": stage, "model": model, "schema_miss": f"{type(e).__name__}: {e}"[:200], "cost": 0.0, **ctx})
            prompt += f"\n\nYour previous reply did not fit the required shape ({type(e).__name__}: {e}). Reply again, in exactly the shape asked for."
    return None
