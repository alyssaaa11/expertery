# Claude's throwaway probe (not project code): find every image-build/runtime problem in one go.
import modal, sys
A="FreeCAD_1.1.4-Linux-x86_64-py311.AppImage"
U="https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/"
img=(modal.Image.from_registry("debian:bookworm-slim")
 .run_commands("apt-get update && apt-get install -y --no-install-recommends ca-certificates curl libgl1 libglib2.0-0 libx11-6 libxext6 libxrender1 libsm6 libice6")
 .run_commands(f"curl -fL -o /opt/{A} {U}{A}", f"curl -fL -o /opt/{A}-SHA256.txt {U}{A}-SHA256.txt",
   f"cd /opt && grep {A} {A}-SHA256.txt | sha256sum -c -",
   f"cd /opt && chmod +x {A} && ./{A} --appimage-extract >/dev/null && rm {A}",
   "ln -s /opt/squashfs-root/usr/bin/freecadcmd /usr/local/bin/freecadcmd",
   "freecadcmd --version || true", "ls /opt/squashfs-root/usr/bin | head -30")
 .add_local_file("run_one_fc.py","/work/run_one_fc.py"))
app=modal.App.lookup("forge-freecad-probe", create_if_missing=True)
with modal.enable_output():
    sb=modal.Sandbox.create(app=app,image=img,block_network=True,cpu=1,memory=(1024,4096),timeout=300)
try:
    def run(*a, env=None):
        p=sb.exec(*a, env=env, timeout=120); out=p.stdout.read(); err=p.stderr.read(); p.wait()
        print("$"," ".join(a),"rc",p.returncode); print(out[-1500:]); print("ERR:",err[-1500:])
    sb.filesystem.write_text(open("M10.py").read(), "/work/answer.py")
    run("freecadcmd","-c","import sys; sys.argv=['run_one_fc.py']; exec(open('/work/run_one_fc.py').read(), {'__name__':'__main__','__file__':'/work/run_one_fc.py'})", env={"FC_SCRATCH":"/work"})
    run("sh","-c","ls -la /work; cat /work/measure.json")
    run("/opt/squashfs-root/usr/bin/python","-c","import urllib.request\ntry:\n urllib.request.urlopen('https://example.com',timeout=5); print('NET OPEN')\nexcept Exception as e: print('NET BLOCKED', type(e).__name__)")
    sb.filesystem.write_text("import cadquery\nresult=None\n", "/work/answer.py")
    run("sh","-c","rm -f /work/answer.step /work/measure.json; cd /work && freecadcmd -c \"import sys; sys.argv=['x']; exec(open('/work/run_one_fc.py').read(), {'__name__':'__main__','__file__':'/work/run_one_fc.py'})\"; echo rc=$?; ls /work")
finally:
    sb.terminate()
