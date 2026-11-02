// Homegrown product page. No tracking, no cookies, no analytics.
const REPLY_TO = "CONTACT_EMAIL";
const MAX_JOB = 600;
const CODE_CAP = 4000;

const EXAMPLES = {
  "L-bracket with 2 holes":
    "An L-shaped mounting bracket: base 80 mm long, 30 mm wide and 5 mm thick, " +
    "upright wall 40 mm tall and 5 mm thick, two 6 mm diameter holes in the base " +
    "20 mm from each end. Overall size 80 x 30 x 45 mm.",
  "Flanged pipe adapter":
    "A flanged pipe adapter: flange disc 90 mm diameter and 8 mm thick with four " +
    "8 mm diameter holes on a 70 mm bolt circle, pipe stub 40 mm outer diameter, " +
    "34 mm inner diameter and 60 mm long. Overall size 90 x 90 x 68 mm.",
  "Electronics box with lid lip":
    "An electronics box: outer box 120 mm long, 80 mm wide and 40 mm tall with " +
    "2 mm walls and an open top, plus a lid 124 mm long, 84 mm wide and 5 mm thick " +
    "with a 3 mm tall lip that fits inside the box. Overall size 124 x 84 x 45 mm."
};

// headline words rise one by one
document.querySelectorAll("#h1 .w > span").forEach((s, i) => {
  s.style.animationDelay = (0.25 + i * 0.08) + "s";
});

// marquee: duplicate content for a seamless loop
const trackEl = document.getElementById("track");
trackEl.innerHTML += trackEl.innerHTML;

// 3D object follows the mouse, teal light follows the cursor
const cardEl = document.getElementById("card");
const objEl = document.getElementById("obj");
cardEl.addEventListener("mousemove", (e) => {
  const r = cardEl.getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width;
  const y = (e.clientY - r.top) / r.height;
  objEl.style.transform = "rotateY(" + ((x - 0.5) * 16) + "deg) rotateX(" + ((0.5 - y) * 10) + "deg) translateZ(20px)";
  cardEl.style.setProperty("--mx", x * 100 + "%");
  cardEl.style.setProperty("--my", y * 100 + "%");
});
cardEl.addEventListener("mouseleave", () => { objEl.style.transform = ""; });

// "Runs privately" toggle
const toggleEl = document.getElementById("toggle");
toggleEl.onclick = () => {
  toggleEl.classList.toggle("off");
  const pair = toggleEl.querySelectorAll("span");
  pair[0].classList.toggle("act");
  pair[1].classList.toggle("act");
};

// scroll reveal + count-up + factory light
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add("in");
    io.unobserve(e.target);
    e.target.querySelectorAll(".count").forEach((c) => {
      const to = +c.dataset.to;
      const dec = +(c.dataset.dec || 0);
      const t0 = performance.now();
      const f = (t) => {
        const p = Math.min((t - t0) / 1400, 1);
        const v = to * (1 - Math.pow(1 - p, 3));
        c.textContent = v.toFixed(dec);
        if (p < 1) requestAnimationFrame(f);
      };
      requestAnimationFrame(f);
    });
    if (e.target.id === "factory") {
      const lit = [...document.querySelectorAll("#flow .node")];
      let i = 0;
      setInterval(() => {
        lit.forEach((n) => n.classList.remove("lit"));
        lit[i % lit.length].classList.add("lit");
        i++;
      }, 900);
    }
  });
}, { threshold: 0.2 });
document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

// ---------- demo panel ----------
const jobBox = document.getElementById("job");
const counter = document.getElementById("counter");
const runBtn = document.getElementById("run");
const timerEl = document.getElementById("timer");
const rowList = [...document.querySelectorAll("#steps li")];
const resultBox = document.getElementById("result");
const askBox = document.getElementById("ask");
const goBox = document.getElementById("golinks");
const apiBox = document.getElementById("apimsg");
const fixNote = document.getElementById("fixnote");
const rowByKey = {};
rowList.forEach((li) => { rowByKey[li.dataset.k] = li; });

function paintCounter() {
  counter.textContent = jobBox.value.length + " / " + MAX_JOB;
}
jobBox.addEventListener("input", paintCounter);
paintCounter();

document.querySelectorAll(".chips button").forEach((b) => {
  b.onclick = () => {
    const full = EXAMPLES[b.textContent];
    jobBox.value = (full || b.textContent).slice(0, MAX_JOB);
    paintCounter();
  };
});

function say(msg) {
  apiBox.textContent = msg;
  apiBox.classList.add("show");
}
function quiet() {
  apiBox.classList.remove("show");
  apiBox.textContent = "";
}
function cap(text, n) {
  text = String(text == null ? "" : text);
  return text.length > n ? text.slice(0, n) : text;
}
function resetRun() {
  rowList.forEach((s) => { s.className = ""; });
  resultBox.classList.remove("show");
  resultBox.textContent = "";
  askBox.classList.remove("show");
  goBox.classList.remove("show");
  fixNote.textContent = "up to 3 rounds";
  rowByKey.measure.querySelector("small").textContent = "size, holes, one solid piece";
}
function rowDetail(key, text) {
  const li = rowByKey[key];
  if (li) li.querySelector("small").textContent = cap(text, 200);
}
function markEvent(ev) {
  const k = ev.step;
  if (k === "write" || k === "build" || k === "measure") {
    rowList.forEach((s) => { if (s.classList.contains("on")) s.classList.replace("on", "done"); });
    rowByKey[k].className = "on";
    if (ev.detail) rowDetail(k, ev.detail);
  } else if (k === "fix") {
    rowList.forEach((s) => { if (s.classList.contains("on")) s.classList.replace("on", "done"); });
    rowByKey.fix.className = "fix";
    if (ev.detail) fixNote.textContent = cap(ev.detail, 200);
  }
}
function startClock(label) {
  const t0 = Date.now();
  timerEl.textContent = label + " · 0 s";
  return setInterval(() => {
    timerEl.textContent = label + " · " + ((Date.now() - t0) / 1000).toFixed(0) + " s";
  }, 200);
}
function chipText(measure) {
  const out = [];
  if (!measure) return out;
  if (measure.solids != null) out.push(measure.solids + (measure.solids === 1 ? " solid" : " solids"));
  const bb = measure.bbox_mm || measure.bbox || measure.extents_mm;
  if (bb && bb.length === 3) out.push(bb.join(" × ") + " mm");
  if (measure.holes != null) out.push(measure.holes + " holes");
  Object.keys(measure).forEach((k) => {
    if (k === "solids" || k === "bbox_mm" || k === "bbox" || k === "extents_mm" || k === "holes") return;
    out.push(k + ": " + measure[k]);
  });
  return out;
}
function showDone(ev, recorded) {
  rowList.forEach((s) => { if (s.classList.contains("on")) s.classList.replace("on", "done"); });
  if (rowByKey.fix.className === "fix") rowByKey.fix.className = "done";
  rowByKey.done.className = "done";
  timerEl.textContent = ev.verdict === "PASS" ? "PASS ✓ · " + recorded : ev.verdict + " · " + recorded;

  const top = document.createElement("div");
  top.className = "topline";
  const badge = document.createElement("span");
  const line = document.createElement("div");
  line.className = "checkline";
  const ref = document.createElement("div");
  ref.className = "refnote";
  if (ev.verdict === "PASS") {
    badge.className = "pass";
    badge.textContent = "Self-check PASS";
    const bit = chipText(ev.measurements).join(" · ");
    line.textContent = "built" + (bit ? " · " + bit + " matches your numbers" : "");
    ref.textContent = "self-check, not the exam referee";
  } else if (ev.verdict === "BUILT") {
    badge.className = "neutral";
    badge.textContent = "Built (size not checked)";
    line.textContent = cap(ev.reason || ev.detail || "the part built but the size could not be checked", 400);
  } else {
    badge.className = "neutral";
    badge.textContent = "Checks failed: see measurements";
    line.textContent = cap(ev.reason || ev.detail || "the part did not pass its checks", 400);
  }
  top.appendChild(badge);
  resultBox.appendChild(top);
  if (line.textContent) resultBox.appendChild(line);
  if (ref.textContent) resultBox.appendChild(ref);

  const chips = document.createElement("div");
  chips.className = "mchips";
  chipText(ev.measurements).forEach((t) => {
    const c = document.createElement("span");
    c.textContent = t;
    chips.appendChild(c);
  });
  if (chips.childNodes.length) resultBox.appendChild(chips);

  if (ev.code) {
    const box = document.createElement("details");
    box.className = "codebox";
    const sum = document.createElement("summary");
    sum.textContent = "Show code";
    const pre = document.createElement("pre");
    pre.textContent = cap(ev.code, CODE_CAP);
    box.appendChild(sum);
    box.appendChild(pre);
    resultBox.appendChild(box);
  }

  const dl = document.createElement("div");
  dl.className = "dl";
  const addLink = (label, url) => {
    if (!url) return;
    const a = document.createElement("a");
    a.textContent = label;
    a.href = url;
    dl.appendChild(a);
  };
  addLink("STL ↓", ev.stl_url);
  addLink("STEP ↓", ev.step_url);
  if (ev.code) {
    const a = document.createElement("a");
    a.textContent = "code ↓";
    a.href = URL.createObjectURL(new Blob([ev.code], { type: "text/plain" }));
    a.download = "part.py";
    dl.appendChild(a);
  }
  if (dl.childNodes.length) resultBox.appendChild(dl);

  if (ev.stl_url && ev.stl_url !== "#") {
    const holder = document.createElement("div");
    holder.className = "viewer";
    resultBox.appendChild(holder);
    initViewer(ev.stl_url, holder);
  }
  resultBox.classList.add("show");
}
async function initViewer(url, holder) {
  try {
    const probe = document.createElement("canvas");
    if (!probe.getContext("webgl")) { holder.style.display = "none"; return; }
    const THREE = await import("three");
    const orbit = await import("three/addons/controls/OrbitControls.js");
    const loaderMod = await import("three/addons/loaders/STLLoader.js");
    const w = holder.clientWidth || 400;
    const h = 300;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    holder.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x101315);
    const cam = new THREE.PerspectiveCamera(45, w / h, 0.1, 10000);
    const ctl = new orbit.OrbitControls(cam, renderer.domElement);
    ctl.autoRotate = true;
    ctl.autoRotateSpeed = 1.0;
    scene.add(new THREE.HemisphereLight(0xffffff, 0x223333, 1.1));
    const lamp = new THREE.DirectionalLight(0xffffff, 1.4);
    lamp.position.set(80, 120, 60);
    scene.add(lamp);
    const geo = await new loaderMod.STLLoader().loadAsync(url);
    geo.computeVertexNormals();
    const mesh = new THREE.Mesh(
      geo,
      new THREE.MeshStandardMaterial({ color: 0xb9c2c7, metalness: 0.9, roughness: 0.35 })
    );
    scene.add(mesh);
    const edge = new THREE.LineSegments(
      new THREE.EdgesGeometry(geo, 30),
      new THREE.LineBasicMaterial({ color: 0x1fa39a })
    );
    mesh.add(edge);
    const box3 = new THREE.Box3().setFromObject(mesh);
    const mid = box3.getCenter(new THREE.Vector3());
    const size = box3.getSize(new THREE.Vector3());
    const far = Math.max(size.x, size.y, size.z) * 2.2;
    cam.position.set(mid.x + far, mid.y + far * 0.7, mid.z + far);
    ctl.target.copy(mid);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    ctl.autoRotate = !reduced;
    const loop = () => {
      requestAnimationFrame(loop);
      ctl.update();
      renderer.render(scene, cam);
    };
    loop();
  } catch (err) {
    holder.style.display = "none";
  }
}
function showErrorEvent(ev) {
  say(cap(ev.detail || ev.message || "Something went wrong building that part.", 400));
}
async function readStream(resp, onEvent) {
  const reader = resp.body.getReader();
  const dec = new TextDecoder();
  let tail = "";
  for (;;) {
    const part = await reader.read();
    if (part.done) break;
    tail += dec.decode(part.value, { stream: true });
    const cut = tail.split("\n\n");
    tail = cut.pop();
    for (const raw of cut) {
      const lines = raw.split("\n");
      for (const ln of lines) {
        const t = ln.trim();
        if (t.indexOf("data:") === 0) {
          try {
            onEvent(JSON.parse(t.slice(5)));
          } catch (err) { /* ignore */ }
        }
      }
    }
  }
}
async function playRecording(label) {
  const resp = await fetch("recorded_run.json");
  const plan = await resp.json();
  const tick = startClock(label);
  try {
    for (const ev of plan) {
      await new Promise((r) => setTimeout(r, 800));
      if (ev.step === "done") {
        showDone(ev, label);
      } else if (ev.step === "error") {
        showErrorEvent(ev);
      } else {
        markEvent(ev);
      }
    }
  } finally {
    clearInterval(tick);
  }
  goBox.classList.add("show");
  askBox.classList.add("show");
}
async function liveRun(job) {
  let resp;
  try {
    resp = await fetch("/api/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job: job })
    });
  } catch (err) {
    say("Could not reach the build service. Please try again.");
    return;
  }
  if (!resp.ok) {
    let msg = "The build service answered " + resp.status + ". Please try again.";
    try {
      const info = await resp.json();
      if (info.message) msg = info.message;
    } catch (err) { /* ignore */ }
    say(cap(msg, 400));
    return;
  }
  const tick = startClock("live run");
  try {
    await readStream(resp, (ev) => {
      if (ev.step === "done") showDone(ev, "live run");
      else if (ev.step === "error") showErrorEvent(ev);
      else markEvent(ev);
    });
  } catch (err) {
    say("The live run dropped. Please try again.");
  } finally {
    clearInterval(tick);
    askBox.classList.add("show");
  }
}
runBtn.onclick = async () => {
  quiet();
  resetRun();
  runBtn.disabled = true;
  try {
    let info;
    try {
      const r = await fetch("/api/status");
      info = await r.json();
    } catch (err) {
      say("Could not reach the demo service. Please try again.");
      return;
    }
    const job = jobBox.value.slice(0, MAX_JOB);
    if (info.state === "paused") {
      say(info.message || "Demo paused: today's budget is used up. Here is a recorded run instead.");
      await playRecording("Recorded run");
    } else if (info.state === "waking") {
      say("Waking up the model (this takes a few minutes). Here is a recorded run meanwhile.");
      await playRecording("Recorded run");
      resetRun();
      await liveRun(job);
    } else {
      await liveRun(job);
    }
  } finally {
    runBtn.disabled = false;
  }
};

// ---------- lead form ----------
const toolBox = document.getElementById("tool");
const mailBox = document.getElementById("email");
const sendBtn = document.getElementById("leadsend");
const formBox = document.getElementById("leadform");
const mailto = document.createElement("a");
mailto.href = "mailto:" + REPLY_TO;
sendBtn.onclick = async () => {
  const payload = { tool: toolBox.value, email: mailBox.value };
  try {
    await fetch("/api/lead", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch (err) { /* ignore */ }
  formBox.textContent = "";
  const done = document.createElement("div");
  done.className = "formdone";
  done.textContent = "Thanks, we read every answer.";
  formBox.appendChild(done);
};
