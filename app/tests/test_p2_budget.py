"""Budget: per-build cost, idle tail, warm-up throttle, paused state."""

import pytest

from app.backend import budget, config


def make(t0=1_700_000_000.0):
    t = [t0]
    return budget.Budget(now=lambda: t[0]), t


def test_one_build_charges_gpu_sandbox_and_one_tail():
    money, _ = make()
    charged = money.charge_build(100.0)
    assert charged == pytest.approx(
        100.0 * config.GPU_USD_PER_S + config.SANDBOX_USD_PER_BUILD
        + config.IDLE_TAIL_USD)


def test_burst_shares_one_tail():
    money, t = make()
    first = money.charge_build(10.0)
    t[0] += 60.0
    second = money.charge_build(10.0)
    assert second == pytest.approx(
        10.0 * config.GPU_USD_PER_S + config.SANDBOX_USD_PER_BUILD)
    assert first - second == pytest.approx(config.IDLE_TAIL_USD)


def test_new_burst_charges_tail_again():
    money, t = make()
    money.charge_build(10.0)
    t[0] += config.BURST_GAP_S + 1.0
    again = money.charge_build(10.0)
    assert again == pytest.approx(
        10.0 * config.GPU_USD_PER_S + config.SANDBOX_USD_PER_BUILD
        + config.IDLE_TAIL_USD)


def test_fired_warmup_charges_wake_once():
    money, t = make()
    assert money.may_warmup("1.2.3.4")
    money.note_warmup("1.2.3.4")
    assert money.spent_today() == pytest.approx(config.WAKE_USD)


def test_second_warmup_within_ten_minutes_not_fired():
    money, t = make()
    money.note_warmup("1.2.3.4")
    t[0] += 60.0
    assert not money.may_warmup("9.9.9.9")  # global throttle
    t[0] += 600.0
    assert not money.may_warmup("1.2.3.4")  # per-IP hour throttle
    assert money.may_warmup("9.9.9.9")
    t[0] += 3600.0
    assert money.may_warmup("1.2.3.4")


def test_spend_at_cap_pauses_status_and_build():
    money, t = make()
    money._spend[budget.day_key(t[0])] = config.DAILY_CAP_USD
    assert money.is_capped()
    state, message = money.status(probe_ok=True)
    assert state == "paused"
    assert "budget" in message.lower()


def test_status_ready_and_waking():
    money, _ = make()
    assert money.status(probe_ok=True)[0] == "ready"
    state, message = money.status(probe_ok=False)
    assert state == "waking"
    assert "recorded run" in message.lower()


def test_status_calls_never_wake_by_themselves():
    money, _ = make()
    before = money.spent_today()
    for _ in range(5):
        money.status(probe_ok=False)
    assert money.spent_today() == before
    assert money._last_warmup is None  # nothing fired
