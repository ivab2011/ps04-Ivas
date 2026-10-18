"""Shared model-call helper used by the editorial and content stages.

- Reads the stage's model from RUN_DIR/config/models.json (the run snapshot).
- Fills prompt templates: every {{KEY}} is replaced by the given value.
- Saves every rendered prompt and raw response to RUN_DIR/llm_calls/ for inspection.
- Tracks token usage and estimates cost when prices are configured (else cost is unknown).
"""
import json, os, time
from datetime import datetime, timezone

USAGE = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cost_known": True}


def model_for(run_dir, stage):
    models = json.load(open(os.path.join(run_dir, "config", "models.json")))
    return models[stage]


def render(template_path, values):
    text = open(template_path, encoding="utf-8").read()
    for key, val in values.items():
        text = text.replace("{{" + key + "}}", val)
    return text


def call(run_dir, stage, prompt, want_json=True, label="call"):
    """Send one prompt; return the response text (parsed dict when want_json)."""
    from openai import OpenAI
    cfg = model_for(run_dir, stage)
    client = OpenAI()
    kwargs = {"model": cfg["model"], "messages": [{"role": "user", "content": prompt}]}
    if want_json:
        kwargs["response_format"] = {"type": "json_object"}
    for attempt in range(3):                      # retry transient API errors
        try:
            res = client.chat.completions.create(**kwargs)
            break
        except Exception as err:
            if attempt == 2:
                raise
            print(f"llm: retry after {type(err).__name__}: {err}", flush=True, file=__import__("sys").stderr)
            time.sleep(5 * (attempt + 1))
    text = res.choices[0].message.content
    usage = getattr(res, "usage", None)
    tin = getattr(usage, "prompt_tokens", 0) or 0
    tout = getattr(usage, "completion_tokens", 0) or 0
    USAGE["calls"] += 1
    USAGE["input_tokens"] += tin
    USAGE["output_tokens"] += tout
    if cfg.get("usd_per_1m_input") is None or cfg.get("usd_per_1m_output") is None:
        USAGE["cost_known"] = False
    else:
        USAGE["cost_usd"] += tin / 1e6 * cfg["usd_per_1m_input"] + tout / 1e6 * cfg["usd_per_1m_output"]
    log_dir = os.path.join(run_dir, "llm_calls")
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    with open(os.path.join(log_dir, f"{stage}-{label}-{stamp}.json"), "w") as f:
        json.dump({"stage": stage, "model": cfg["model"], "prompt": prompt, "response": text,
                   "input_tokens": tin, "output_tokens": tout}, f, indent=1)
    return json.loads(text) if want_json else text


def usage_summary():
    """Return 'calls tokens_in tokens_out cost' where cost is a number or null."""
    cost = round(USAGE["cost_usd"], 4) if USAGE["cost_known"] else "null"
    return f"{USAGE['calls']} {USAGE['input_tokens']} {USAGE['output_tokens']} {cost}"
