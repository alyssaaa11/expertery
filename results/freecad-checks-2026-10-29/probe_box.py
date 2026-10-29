# Claude's throwaway probe: run check_hand/check_safety with the two known box bugs patched around (not project code).
import sys; sys.path.insert(0, "."); sys.path.insert(1, "~/projects/forge/experiments/freecad")
import modal, cloud_exec as ce, cloud_grade_probe as g
from modal.exception import SandboxFilesystemNotFoundError
class FS:
    def __init__(s, fs): s.fs = fs
    def write_text(s, path, data): return s.fs.write_text(data, path)   # bug A: arguments reversed
    def read_bytes(s, p):
        try: return s.fs.read_bytes(p)
        except SandboxFilesystemNotFoundError: raise FileNotFoundError(p)  # bug B: Modal's exception type
    def read_text(s, p):
        try: return s.fs.read_text(p)
        except SandboxFilesystemNotFoundError: raise FileNotFoundError(p)
class SB:
    def __init__(s, sb): s.sb = sb; s.filesystem = FS(sb.filesystem)
    def __getattr__(s, n): return getattr(s.sb, n)
fac = lambda: SB(ce.build_sandbox())
ex = lambda src: ce.run_answer_in_box(src, sandbox_factory=fac)
with modal.enable_output():
    with g._app.run():
        print("=== HAND"); ce.check_hand(exec_fn=ex, grade_fn=g.grade.remote)
        print("=== SAFETY"); ce.check_safety(exec_fn=ex, grade_fn=g.grade.remote)
