"""Offline tests for the factory generator (no network, no model calls).

Reference programs are trusted generator code and may run locally
(per MUSE_SPEC section 2). Never opens blind/ folders or
expected*.json contents.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import generator
import make_jobs

pytest.importorskip("cadquery")


def test_ten_families_twenty_jobs_each():
    jobs = generator.generate_all()
    assert len(jobs) == 200
    for family in range(1, 11):
        sub = [j for j in jobs if j["family"] == family]
        assert len(sub) == 20
        assert [j["id"] for j in sub] == [
            "F%d-%d" % (family, n) for n in range(1, 21)]
    for job in jobs:
        assert job["text"] and job["reference"]
        assert "result" in job["reference"]


def test_deterministic_same_seed_same_file():
    assert generator.generate_all() == generator.generate_all()
    assert generator.choose_dev_ids(
        generator.generate_all()) == generator.choose_dev_ids(
            generator.generate_all())


def test_dev_split_two_per_family():
    jobs = generator.generate_all()
    dev = generator.choose_dev_ids(jobs)
    assert len(dev) == 20
    for family in range(1, 11):
        assert len([d for d in dev
                    if d.startswith("F%d-" % family)]) == 2


@pytest.mark.parametrize("family", list(range(1, 11)))
def test_references_build_one_valid_solid(family):
    import random as _random

    rng = _random.Random(generator.SEED)
    params = None
    for fam in range(1, family + 1):
        for n in range(generator.JOBS_PER_FAMILY):
            params = generator.FAMILIES[fam]["gen"](rng)
            if fam == family and n in (0, generator.JOBS_PER_FAMILY - 1):
                shape = generator.build_source(
                    generator.FAMILIES[fam]["src"](params))
                n_solids, valid = generator.shape_info(shape)
                assert (n_solids, valid) == (1, True)


@pytest.mark.parametrize("family", list(range(1, 11)))
def test_wrong_variants_fail_at_tight(family):
    fam = generator.FAMILIES[family]
    params = generator.first_params(family)
    ref = generator.build_source(fam["src"](params))
    wrongs = fam["wrong"](params)
    assert len(wrongs) == 2
    for override in wrongs:
        passed, fails = generator.score_at_tight(fam["src"](override),
                                                ref)
        assert not passed, "wrong variant PASSED at 1e-6: %s" % (fails,)


def test_no_job_text_near_an_exam_text():
    jobs = generator.generate_all()
    texts = make_jobs.exam_texts()
    assert len(texts) >= 30
    worst = max(make_jobs.max_overlap(j["text"], texts) for j in jobs)
    assert worst < 0.9


def test_self_check_table_ok_on_real_jobs():
    jobs = generator.generate_all()
    rows = make_jobs.self_check(jobs, make_jobs.exam_texts())
    assert len(rows) == 10
    for _fam, _name, n_valid, n_jobs, wrongs, ratio, n_text_ref in rows:
        assert n_valid == n_jobs == 20
        assert len(wrongs) == 2
        assert all(not passed for passed, _f in wrongs)
        assert ratio < 0.9
        assert n_text_ref == n_jobs == 20
    assert make_jobs.print_table(rows) is True


@pytest.mark.parametrize("family", list(range(1, 11)))
def test_text_ref_passes_on_every_generated_job(family):
    jobs = [j for j in generator.generate_all()
            if j["family"] == family]
    assert len(jobs) == 20
    for job in jobs:
        ok, missing = make_jobs.text_ref_ok(job["text"],
                                            job["reference"])
        assert ok, "%s: reference uses %s, not in the text" % (
            job["id"], missing)


def test_text_ref_fails_on_rounded_mismatch():
    # A family whose text prints 21.2 while its reference uses 21.3
    # fails TEXT=REF.
    jobs = generator.generate_all()
    job = next(j for j in jobs if j["family"] == 3)
    ok, _missing = make_jobs.text_ref_ok(job["text"], job["reference"])
    assert ok
    body = make_jobs.body_of(job["reference"])
    nums = make_jobs.NUM_RE.findall(body)
    assert nums, "F3 reference body has no numeric literals"
    texts = [float(m) for m in make_jobs.NUM_RE.findall(job["text"])]
    victim, shifted = None, None
    for m in nums:
        if float(m) == int(float(m)) \
                and abs(int(float(m))) <= make_jobs.SMALL_INT:
            continue
        cand = round(float(m) + 0.1, 1)
        if all(abs(cand - t) > 1e-9 for t in texts):
            victim, shifted = m, str(cand)
            break
    assert victim is not None, "no shiftable literal in F3 reference"
    bad_ref = body.replace(victim, shifted, 1)
    ok, missing = make_jobs.text_ref_ok(job["text"], bad_ref)
    assert not ok
    assert missing == shifted
