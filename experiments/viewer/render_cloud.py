#!/usr/bin/env python3
"""Answer-viewer renderer: SVG pictures from inside the cloud CadQuery box.

One static-viewer run needs two pictures per answer (Glimmer's part next to
the correct part). AI-written answer code never runs on the Mac, so both
pictures render inside the cloud box: one Modal sandbox built with
cloud_cq's image and sandbox_kwargs (network blocked, lifetime <= 2 h).

Reuse by import (never copied): cloud_cq.build_image / sandbox_kwargs /
EXEC_TIMEOUT_S / RUN script path, gallery.SVG_OPT + fit_viewbox_to_drawing.

Protocol per item (sequential, in ONE sandbox):
  1. write the code to /work/answer.py,
  2. run the SAME runner script as the grader (``python run_cq_box.py
     /work`` with the same 60 s limit), so ``result`` is taken the same
     way; a missing BREP is the answer's ERROR (never raised),
  3. run a small trusted SVG-export snippet (BREP in, SVG out, with
     gallery's SVG_OPT), read back /work/shape.svg,
  4. fit the viewBox locally (pure string edit, no code runs on the Mac).

References are trusted generator code but render in the same box too
(simplest and the same view): the caller just passes them as items.

Cost: ``render_svgs(items, budget_dollars)`` stops before a new item once
``elapsed_sandbox_seconds * SANDBOX_DOLLARS_PER_SECOND`` exceeds the
budget; unrendered ids come back as BUDGET STOP text. Modal is imported
lazily so the pure helpers (cost math, per-item loop) are unit-testable
offline; tests inject a fake sandbox factory and a fake clock.
"""

import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_DIR = os.path.join(os.path.dirname(HERE), "final")
FACTORY_DIR = os.path.join(os.path.dirname(HERE), "factory")
for _p in (HERE, FINAL_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cloud_cq  # noqa: E402 (lazy Modal inside; reuse by import)

try:
    import modal
except ImportError:  # offline: pure helpers still work; runs refuse
    modal = None


def _load_gallery():
    """The factory gallery module, by file path (only SVG_OPT + the
    viewBox fitter are used; nothing runs)."""
    spec = importlib.util.spec_from_file_location(
        "viewer_gallery", os.path.join(FACTORY_DIR, "gallery.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gallery = _load_gallery()
SVG_OPT = dict(_gallery.SVG_OPT)
_fit_viewbox_to_drawing = _gallery.fit_viewbox_to_drawing

APP_NAME = "forge-viewer"
MAX_LIFETIME_S = 2 * 3600  # one reused box lives at most 2 h
EXEC_TIMEOUT_S = cloud_cq.EXEC_TIMEOUT_S  # same 60 s limit as grading
WORK_DIR = cloud_cq.WORK_DIR
RUN_SCRIPT = WORK_DIR + "/" + cloud_cq.RUN_SCRIPT
ANSWER_PATH = WORK_DIR + "/" + cloud_cq.ANSWER_NAME
SVG_PATH = WORK_DIR + "/shape.svg"

# Assumed box rate for the --budget hard stop: sandbox seconds times this
# rate is the estimated spend. (cloud_cq pins the box shape -- cpu 1,
# 1-4 GiB -- but no dollar rate, so the rate lives here, next to the
# stop logic that uses it, and stays overridable per call.)
SANDBOX_DOLLARS_PER_SECOND = 0.0001

ERROR_PREFIX = "ERROR: "
BUDGET_PREFIX = "BUDGET STOP: "
NO_BREP_PREFIX = "the answer wrote no BREP"

SVG_SNIPPET = (
    "from cadquery import importers as _imp, "
    "exporters as _exp\n"
    "_shape = _imp.importShape(_imp.ImportTypes.BREP, "
    "'/work/answer.brep').val()\n"
    "_exp.export(_shape, '/work/shape.svg', exportType='SVG', opt=%s)\n"
    % (repr(dict(SVG_OPT)),)
)


def estimate_cost(elapsed_seconds):
    """Estimated spend for elapsed sandbox seconds at the box rate."""
    return max(0.0, float(elapsed_seconds)) * SANDBOX_DOLLARS_PER_SECOND


def over_budget(elapsed_seconds, budget_dollars):
    """True once the estimated spend exceeds the budget (hard stop)."""
    return estimate_cost(elapsed_seconds) > float(budget_dollars)


def sandbox_lifetime_s(n_items=0, per_item_s=2 * EXEC_TIMEOUT_S):
    """Box lifetime for a batch: per-item allowance, capped at 2 h."""
    return min(MAX_LIFETIME_S, max(60, int(n_items) * int(per_item_s)))


def box_kwargs(lifetime_s=None):
    """cloud_cq's sandbox kwargs with the viewer lifetime (<= 2 h).

    Network stays blocked (inherited from cloud_cq.sandbox_kwargs)."""
    kwargs = dict(cloud_cq.sandbox_kwargs())
    kwargs["timeout"] = min(MAX_LIFETIME_S,
                            int(lifetime_s or MAX_LIFETIME_S))
    return kwargs


def build_image():
    """The box image: cloud_cq's (CadQuery + the runner script)."""
    return cloud_cq.build_image()


def render_one_in_box(sandbox, code):
    """Render one code string with a live (or fake) sandbox.

    Returns the SVG text, or an ERROR text when the answer wrote no
    shape / exported nothing. Never raises for a bad answer.
    """
    try:
        sandbox.filesystem.write_text(
            data=code or "", remote_path=ANSWER_PATH)
        sandbox.exec("python", RUN_SCRIPT, WORK_DIR,
                     timeout=EXEC_TIMEOUT_S)
        try:
            sandbox.filesystem.read_bytes(
                remote_path=cloud_cq.BREP_PATH)
        except Exception:
            return "%s%s" % (ERROR_PREFIX, NO_BREP_PREFIX)
        sandbox.exec("python", "-c", SVG_SNIPPET, timeout=EXEC_TIMEOUT_S)
        svg_text = sandbox.filesystem.read_text(remote_path=SVG_PATH)
        if not isinstance(svg_text, str):
            svg_text = svg_text.decode("utf-8", "replace")
        if "<svg" not in svg_text:
            return "%sempty SVG export" % (ERROR_PREFIX,)
        return _fit_viewbox_to_drawing(svg_text)
    except Exception as e:  # noqa: BLE001 -- a bad answer is text
        return "%s%r" % (ERROR_PREFIX, e)


def render_items(items, sandbox_factory, budget_dollars=0.30,
                 clock=None):
    """Render items in ONE sandbox from sandbox_factory (no args).

    items: [{id, code}]. Stops before a new item once the budget is
    exceeded; unrendered ids get BUDGET STOP text. Returns
    (results, elapsed_seconds, est_cost): results maps every input id to
    svg_text | error_text (every id is always present).
    """
    now = clock or time.monotonic
    results = {}
    t_start = now()
    sandbox = sandbox_factory()
    try:
        for item in items or []:
            item_id = item.get("id")
            if over_budget(now() - t_start, budget_dollars):
                results[item_id] = (
                    "%ssandbox budget $%.2f exceeded; re-run with a "
                    "larger --budget" % (BUDGET_PREFIX, budget_dollars))
                continue
            results[item_id] = render_one_in_box(sandbox,
                                                item.get("code"))
    finally:
        try:
            sandbox.terminate()
        except Exception:  # noqa: BLE001 -- terminate is best-effort
            pass
    elapsed = now() - t_start
    return results, elapsed, estimate_cost(elapsed)


def render_local(items, budget_dollars=0.30, sandbox_factory=None,
                 clock=None):
    """Offline entry point (tests + make_viewer injection).

    Without a sandbox_factory there is nothing to render with and no
    Modal run is ever started here: every id comes back as ERROR text.
    """
    if sandbox_factory is None:
        return ({i.get("id"): "%soffline (no sandbox factory)"
                 % (ERROR_PREFIX,) for i in items or []}, 0.0, 0.0)
    return render_items(items, sandbox_factory, budget_dollars, clock)


if modal is not None:
    _viewer_image = None

    def _image():
        global _viewer_image
        if _viewer_image is None:
            _viewer_image = build_image()
        return _viewer_image

    _app = modal.App(APP_NAME)

    @_app.function(image=_image(), cpu=cloud_cq.CPU, timeout=MAX_LIFETIME_S)
    def render_svgs(items, budget_dollars=0.30):
        """Render [{id, code}] to {id: svg_text | error_text} in ONE box.

        The sandbox reuses cloud_cq's image and sandbox_kwargs with a
        capped lifetime; each answer runs under the same 60 s limit as
        grading. A Modal-side hard stop mirrors the budget.
        """
        lifetime = sandbox_lifetime_s(len(items or []))

        def _factory():
            app = cloud_cq.lookup_exec_app()
            return modal.Sandbox.create(app=app, image=_image(),
                                        **box_kwargs(lifetime))

        results, _elapsed, _cost = render_items(
            items, _factory, budget_dollars)
        return results
else:
    def render_svgs(items, budget_dollars=0.30):  # noqa: E306
        """Offline stand-in: refuses (tests inject fakes instead)."""
        raise RuntimeError("modal is not installed; cannot render SVGs")
