"""Limits: job length, per-IP hourly rate, concurrency, IPs, run ids, leads."""

import re
import time

from app.backend import limits


def test_job_over_limit_rejected():
    code, message = limits.check_job("x" * 601)
    assert code == 413
    assert "600" in message


def test_job_at_limit_allowed():
    assert limits.check_job("x" * 600) is None


def test_empty_job_rejected():
    assert limits.check_job("   ")[0] == 413


def test_fifth_build_in_an_hour_rejected():
    t = [1000.0]
    rates = limits.RateState(now=lambda: t[0])
    for _ in range(4):
        assert rates.check_ip("1.2.3.4") is None
        rates.note_build("1.2.3.4")
    code, message = rates.check_ip("1.2.3.4")
    assert code == 429
    assert "wait" in message.lower()


def test_other_ip_unaffected_and_hour_prunes():
    t = [1000.0]
    rates = limits.RateState(now=lambda: t[0])
    for _ in range(4):
        rates.note_build("1.2.3.4")
    assert rates.check_ip("5.6.7.8") is None
    t[0] += 3601.0
    assert rates.check_ip("1.2.3.4") is None


def test_third_concurrent_build_rejected():
    rates = limits.RateState()
    assert rates.try_acquire() is None
    assert rates.try_acquire() is None
    code, message = rates.try_acquire()
    assert code == 429
    assert "Busy" in message
    rates.release()
    assert rates.try_acquire() is None
    rates.release()
    rates.release()
    assert rates.active == 0


def test_client_ip_ignores_spoofed_first_hop():
    assert limits.client_ip("spoofed, 9.9.9.9", "peer") == "9.9.9.9"
    assert limits.client_ip("9.9.9.9", "peer") == "9.9.9.9"
    assert limits.client_ip("", "peer") == "peer"


def test_run_ids_are_32_hex_uuid4():
    seen = {limits.new_run_id() for _ in range(50)}
    assert len(seen) == 50
    for rid in seen:
        assert re.fullmatch(r"[0-9a-f]{32}", rid)


def test_lead_rejects_long_email():
    assert limits.check_lead("tool", "a" * 195 + "@b.co") is None  # 200 ok
    code, _ = limits.check_lead("tool", "a" * 196 + "@b.co")  # 201 rejected
    assert code == 400


def test_lead_lengths():
    assert limits.check_lead("t" * 300, "a@b.com") is None
    assert limits.check_lead("t" * 301, "a@b.com")[0] == 400
    assert limits.check_lead("tool", "not-an-email")[0] == 400


def test_lead_record_shape_and_no_stdout(capsys):
    rec = limits.lead_record("my tool", "me@company.com", ts=123.0)
    assert rec == {"tool": "my tool", "email": "me@company.com",
                   "ts": 123.0}
    assert capsys.readouterr().out == ""


def test_lead_check_prints_nothing(capsys):
    limits.check_lead("tool", "a" * 201 + "@x.com")
    assert capsys.readouterr().out == ""
    assert time.time() > 0  # sanity: fake-clock-free part ran
