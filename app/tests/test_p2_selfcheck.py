"""self_check: PASS / BUILT / CHECK FAILED rules and every pattern."""

from app.backend import selfcheck

BOX_80_30_45 = {"bbox": [0, 0, 0, 80, 30, 45], "volume": 1000.0,
                "solids": 1}


def test_correct_box_passes():
    verdict, reasons = selfcheck.self_check(
        "An L bracket. Overall size 80 x 30 x 45 mm.", BOX_80_30_45)
    assert verdict == "PASS"
    assert any("matches your numbers" in r for r in reasons)


def test_two_solids_fail():
    meas = dict(BOX_80_30_45, solids=2)
    verdict, _ = selfcheck.self_check(
        "An L bracket. Overall size 80 x 30 x 45 mm.", meas)
    assert verdict == "CHECK FAILED"


def test_wrong_extent_fails():
    meas = dict(BOX_80_30_45, bbox=[0, 0, 0, 81, 30, 45])
    verdict, reasons = selfcheck.self_check(
        "An L bracket. Overall size 80 x 30 x 45 mm.", meas)
    assert verdict == "CHECK FAILED"
    assert reasons


def test_no_stated_size_is_built_never_pass():
    verdict, reasons = selfcheck.self_check(
        "Make a nice bracket with two holes.", BOX_80_30_45)
    assert verdict == "BUILT"
    assert any("size not checked" in r for r in reasons)


def test_ambiguous_text_is_built():
    verdict, _ = selfcheck.self_check(
        "A bracket about 80 mm long with some holes in it.", BOX_80_30_45)
    assert verdict == "BUILT"


def test_overall_pattern_with_unicode_times():
    name, dims = selfcheck.parse_overall_size(
        "Overall dimensions 80 \u00d7 30 \u00d7 45 mm")
    assert name == "OVERALL"
    assert dims == (80.0, 30.0, 45.0)


def test_box_noun_pattern():
    name, dims = selfcheck.parse_overall_size(
        "Mill an 80 x 30 x 45 mm block from aluminium.")
    assert name == "BOXNOUN"
    verdict, _ = selfcheck.self_check(
        "Mill an 80 x 30 x 45 mm block from aluminium.", BOX_80_30_45)
    assert verdict == "PASS"


def test_base_wall_pattern_adds_height():
    job = ("An L bracket: base 80 x 30 x 5 mm, upright wall 40 mm tall "
           "and 5 mm thick.")
    name, dims = selfcheck.parse_overall_size(job)
    assert name == "BASE_WALL"
    assert dims == (80.0, 30.0, 45.0)
    verdict, _ = selfcheck.self_check(job, BOX_80_30_45)
    assert verdict == "PASS"


def test_bare_base_is_not_an_overall_size():
    name, dims = selfcheck.parse_overall_size(
        "A base 80 x 30 x 5 mm with two studs on top.")
    assert (name, dims) == (None, None)
    verdict, _ = selfcheck.self_check(
        "A base 80 x 30 x 5 mm with two studs on top.", BOX_80_30_45)
    assert verdict == "BUILT"


def test_axis_order_does_not_matter():
    verdict, _ = selfcheck.self_check(
        "Overall size 45 x 80 x 30 mm.",
        {"bbox": [0, 0, 0, 80, 30, 45], "volume": 1.0, "solids": 1})
    assert verdict == "PASS"


def test_half_percent_tolerance():
    ok = {"bbox": [0, 0, 0, 80.4, 30, 45], "volume": 1.0, "solids": 1}
    verdict, _ = selfcheck.self_check(
        "Overall size 80 x 30 x 45 mm.", ok)
    assert verdict == "PASS"  # 0.5% over reads as a match
    bad = {"bbox": [0, 0, 0, 80.5, 30, 45], "volume": 1.0, "solids": 1}
    verdict, _ = selfcheck.self_check(
        "Overall size 80 x 30 x 45 mm.", bad)
    assert verdict == "CHECK FAILED"


def test_recorded_style_measurements():
    meas = {"bbox_mm": [80.0, 30.0, 45.0], "solids": 1}
    verdict, _ = selfcheck.self_check(
        "Overall size 80 x 30 x 45 mm.", meas)
    assert verdict == "PASS"


def test_unbuilt_part_fails():
    assert selfcheck.self_check("Overall size 1 x 2 x 3 mm.",
                                None)[0] == "CHECK FAILED"
    assert selfcheck.self_check("Overall size 1 x 2 x 3 mm.",
                                {})[0] == "CHECK FAILED"


def test_every_pattern_has_a_name():
    assert selfcheck.pattern_names() == ["OVERALL", "BOXNOUN", "BASE",
                                         "BASE_WALL"]
