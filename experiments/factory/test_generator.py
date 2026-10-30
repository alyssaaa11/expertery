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
    for _fam, _name, n_valid, n_jobs, wrongs, ratio, n_text_ref, \
            n_cuts in rows:
        assert n_valid == n_jobs == 20
        assert len(wrongs) == 2
        assert all(not passed for passed, _f in wrongs)
        assert ratio < 0.9
        assert n_text_ref == n_jobs == 20
        assert n_cuts == n_jobs == 20
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
    assert make_jobs.NUM_RE.findall(body), \
        "F3 reference body has no numeric literals"
    texts = [float(m) for m in make_jobs.NUM_RE.findall(job["text"])]
    spans = make_jobs._divisor_spans(body)
    victim = None
    for m in make_jobs.NUM_RE.finditer(body):
        s, e = m.span()
        v = float(m.group())
        if v == int(v) and abs(int(v)) <= 1:
            continue
        if any(ds <= s and e <= de for ds, de in spans):
            continue
        cand = round(v + 0.1, 1)
        if all(abs(cand - t) > 1e-9 for t in texts):
            victim = (s, e, str(cand))
            break
    assert victim is not None, "no shiftable literal in F3 reference"
    s, e, shifted = victim
    bad_ref = body[:s] + shifted + body[e:]
    ok, missing = make_jobs.text_ref_ok(job["text"], bad_ref)
    assert not ok
    assert missing == shifted


def test_text_ref_flags_unprinted_integer_size():
    # Verifier H2: TEXT=REF exempts only 0, +-1 and the /2 of a printed
    # size. A reference box Y -3..3 against the text "5.9 wide" fails.
    ok, _missing = make_jobs.text_ref_ok(
        "A plate 5.9 wide.",
        "s = s.cut(_box(0, 5, -3, 3, 0, 1))\nresult = s\n")
    assert not ok


def test_cuts_ok_on_every_generated_job():
    for job in generator.generate_all():
        ok, detail = make_jobs.cuts_ok(job["reference"])
        assert ok, "%s: %s" % (job["id"], detail)


def _old_two_bore_src5():
    """The pre-round-1d F5 source: two overlapping coaxial bore cuts."""
    p = generator.first_params(5)
    new = generator.FAMILIES[5]["src"](p)
    dm = generator.num(round(p["rm"] * 2, 1))
    Lm = generator.num(p["Lm"])
    single = ("s = s.cut(_xcyl((%s)/2, 0, 0, (-6 - 1), (%s + 1)))"
              % (dm, Lm))
    assert single in new
    two = ("s = s.cut(_xcyl((%s)/2, 0, 0, -1, (%s + 1)))\n"
           "s = s.cut(_xcyl((%s)/2, 0, 0, -7, 1))") % (dm, Lm, dm)
    return new.replace(single, two)


def test_cuts_fails_on_overlapping_coaxial_cuts():
    # The old F5 reference cuts the main bore as two overlapping
    # coaxial cylinders. Same solid (one valid solid), but CUTS fails.
    old = _old_two_bore_src5()
    ok, detail = make_jobs.cuts_ok(old)
    assert not ok, "overlapping coaxial cuts passed CUTS: %s" % (detail,)
    n_solids, valid = generator.shape_info(generator.build_source(old))
    assert (n_solids, valid) == (1, True)


def test_f10_no_cut_below_top_face():
    # Round 1d fix 2: nothing but the recess and the spout bore reaches
    # below the top face H. The slab Z H-1..H holds the body cone minus
    # the recess (both described by the text); the rim lives above H,
    # the spout and the bore top out far below. Checked against the
    # analytic frustum volumes, an independent oracle.
    import math

    import cadquery as _cq

    p = generator.first_params(10)
    ref = generator.build_source(generator.FAMILIES[10]["src"](p))
    c = generator._c10(p)  # the canonical numbers the text prints
    H = c["H"]
    Rb, Rt = c["Db"] / 2, c["Dt"] / 2
    rrb, rrt = c["Drb"] / 2, c["Drt"] / 2
    tf = c["tf"]
    body_R0 = Rb + (Rt - Rb) * (H - 1) / H
    v_body = math.pi / 3 * (body_R0 ** 2 + body_R0 * Rt + Rt ** 2)
    rec_r0 = rrb + (rrt - rrb) * (H - 1 - tf) / (H + 1 - tf)
    rec_r1 = rrb + (rrt - rrb) * (H - tf) / (H + 1 - tf)
    v_rec = math.pi / 3 * (rec_r0 ** 2 + rec_r0 * rec_r1 + rec_r1 ** 2)
    slab = _cq.Solid.makeBox(200, 200, 1,
                             _cq.Vector(-100, -100, H - 1))
    got = ref.intersect(slab).Volume()
    assert got == pytest.approx(v_body - v_rec, rel=1e-6)
