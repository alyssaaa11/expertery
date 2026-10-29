"""Offline tests for experiments/train/forge_train.py (no GPU, no network)."""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import forge_train

FT = os.path.join(os.path.dirname(HERE), "first-test")
if FT not in sys.path:
    sys.path.insert(0, FT)
import runner


class FakeTok:
    """Minimal tokenizer with a chat template (word tokens)."""

    eos_token = ""

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=False):
        text = "".join(
            "[%s]%s[/%s]" % (m["role"], m["content"], m["role"]) for m in msgs
        )
        if add_generation_prompt:
            text += "[assistant]"
        return text

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": text.split()}


class SkewTok(FakeTok):
    """Template that renders history differently, forcing the fallback."""

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=False):
        if add_generation_prompt:
            return "PROMPT>" + msgs[-1]["content"]
        return "FULL>" + " | ".join(m["content"] for m in msgs)


def test_system_prompt_matches_first_test():
    assert forge_train.SYSTEM_PROMPT == runner.SYSTEM_PROMPT


def test_labels_masked_before_answer():
    tok = FakeTok()
    enc = forge_train.encode_example(tok, "make a box", "result = 1")
    assert not enc["dropped"]
    prompt, full = forge_train.render_full(tok, "make a box", "result = 1")
    n_prompt = len(tok(prompt)["input_ids"])
    assert enc["input_ids"] == tok(full)["input_ids"]
    assert enc["labels"][:n_prompt] == [-100] * n_prompt
    assert enc["labels"][n_prompt:] == enc["input_ids"][n_prompt:]
    assert any(v != -100 for v in enc["labels"])  # answer part really trained


def test_fallback_render_when_template_skews_history():
    tok = SkewTok()
    prompt, full = forge_train.render_full(tok, "make a box", "result = 1")
    assert full.startswith(prompt)  # fallback = prompt + answer
    enc = forge_train.encode_example(tok, "make a box", "result = 1")
    assert not enc["dropped"]
    n_prompt = len(tok(prompt)["input_ids"])
    assert enc["labels"][:n_prompt] == [-100] * n_prompt


def test_long_examples_dropped_and_counted():
    tok = FakeTok()
    short = {"text": "box", "code": "result = 1"}
    long = {"text": "big " * 200, "code": "result = 1"}
    enc = forge_train.encode_example(tok, long["text"], long["code"], max_tokens=50)
    assert enc["dropped"] and enc["tokens"] > 50
    kept, dropped = forge_train.filter_batch(tok, [short, long, short], max_tokens=50)
    assert len(kept) == 2 and dropped == 1


def test_cap_timeout_math():
    assert forge_train.seconds_for_dollars(3.95, 3.95) == pytest.approx(3600.0)
    assert forge_train.dollars_for_seconds(3600.0, 2.50) == pytest.approx(2.50)
    plan = forge_train.plan_timeouts(
        3.0, [("train", 3.95, 600), ("serve", 2.50, 600)]
    )
    assert plan["train"] == 600 and plan["serve"] == 600
    assert plan["_left"] == pytest.approx(
        3.0 - forge_train.dollars_for_seconds(600, 3.95)
        - forge_train.dollars_for_seconds(600, 2.50),
        abs=0.01,  # plan rounds money left to cents
    )


def test_cap_refuses_step_that_does_not_fit():
    with pytest.raises(forge_train.CapExceeded):
        forge_train.plan_timeouts(0.01, [("train", 3.95, 600)])
    # First step fits, second does not: the second is refused.
    with pytest.raises(forge_train.CapExceeded):
        forge_train.plan_timeouts(0.10, [("train", 3.95, 60), ("merge", 3.95, 600)])


def test_smoke_entrypoint_refuses_tiny_cap_offline():
    assert forge_train.main(["smoke", "--cap-dollars", "0.01"]) == 2


def test_returns_are_plain_json():
    out = forge_train.ensure_plain_json(
        {"params": {1, 2}, "when": (1, 2), "nested": [{"x": frozenset((3,))}]}
    )
    json.dumps(out)  # must serialize without a custom default
    assert isinstance(out, dict)
    for v in out.values():
        assert isinstance(v, (dict, list, str, int, float, bool, type(None)))
