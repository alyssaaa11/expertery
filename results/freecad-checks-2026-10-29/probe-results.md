# Free cloud probes, 2026-10-29 (Claude, trusted code only; probe scripts copied here as records)
- verified: `cloud_exec.py --check-image` (fd43235) prints `FreeCAD 1.1.4 Revision: 20260928` (image.txt).
- verified: --check-hand / --check-safety crash: `Sandbox.filesystem.write_text() currently only supports absolute
  remote_path values` (code passes (path, data); Modal 1.6.3 signature is write_text(data, remote_path)).
- verified: --check-refs crashes: `App is already running and can't be started again` (App.lookup(...).run()).
- verified: grader image lacks libGL (`ImportError: libGL.so.1`); with apt libgl1 libglib2.0-0 libxrender1 libx11-6
  libxext6 and the defining App's .run(): `REFS 30/30 PASS`.
- verified (box bugs patched around in probe_box.py): hand answers H13, H6, M1, M10, M6 PASS; H13_wrong, M1_wrong
  FAIL (5/2 as on the Mac); max relative bbox/volume difference vs Mac FreeCAD 2.5e-9 .. 6.4e-8 (Mac arm64 vs Linux
  x86 float differences), above the 1e-9 gate, far below the 1e-6 strict referee.
- verified: SAFETY OK: typo → AttributeError; `import cadquery` refused; network → URLError (name resolution); the
  listing probe found 0 jobs/expected/reference files.
- verified: missing file in the box raises modal.exception.SandboxFilesystemNotFoundError (not FileNotFoundError).
