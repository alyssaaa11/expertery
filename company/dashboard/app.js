/* Renders window.QOW_DATA (written by build_data.py) into the page.
   Offline: no fetch, no network requests of any kind. */
(function () {
  var d = window.QOW_DATA;
  if (!d) {
    document.body.insertAdjacentHTML("afterbegin", "<p>Missing data.js: run build_data.py first.</p>");
    return;
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  document.getElementById("fiction-banner").textContent = d.banner;
  document.getElementById("company-about").textContent = d.company.about;
  document.getElementById("company-badge").textContent = d.company.badge;
  document.getElementById("programmes").textContent =
    "Programmes: " + d.company.programmes.join(", ");
  document.getElementById("footer-note").textContent =
    d.banner + " · " + d.company.name;

  d.company.teams.forEach(function (t) {
    var c = el("div", "card");
    c.appendChild(el("h3", null, t.name));
    c.appendChild(el("p", null, t.blurb));
    document.getElementById("team-cards").appendChild(c);
  });

  var tools = d.tools;
  var toolCards = [
    { name: tools.keel.name, blurb: tools.keel.blurb + " Version " + tools.keel.version + ".",
      extra: "Manual: company/manual.md", status: tools.keel.status },
    { name: tools.gauge.name, blurb: tools.gauge.blurb, status: tools.gauge.status },
    { name: tools.assistant.name, blurb: tools.assistant.blurb, status: tools.assistant.status },
  ];
  toolCards.forEach(function (t, i) {
    var c = el("div", "card" + (i === 0 ? " accent" : ""));
    c.appendChild(el("h3", null, t.name));
    c.appendChild(el("p", null, t.blurb));
    if (t.extra) c.appendChild(el("p", null, t.extra));
    var s = el("p", null, "Status: ");
    var live = t.status === "live";
    s.appendChild(el("span", "status " + (live ? "live" : "wait"), t.status));
    c.appendChild(s);
    document.getElementById("tool-cards").appendChild(c);
  });

  var kfBody = document.querySelector("#kf-table tbody");
  tools.kf.forEach(function (row) {
    var tr = el("tr");
    tr.appendChild(el("td", null, row.code));
    tr.appendChild(el("td", null, row.hole));
    tr.appendChild(el("td", null, row.counterbore));
    tr.appendChild(el("td", null, row.countersink));
    kfBody.appendChild(tr);
  });

  var matBody = document.querySelector("#materials-table tbody");
  tools.materials.forEach(function (row) {
    var tr = el("tr");
    tr.appendChild(el("td", null, row.code));
    tr.appendChild(el("td", null, row.name));
    tr.appendChild(el("td", null, row.wall));
    tr.appendChild(el("td", null, row.fillet));
    tr.appendChild(el("td", null, row.min_wall));
    matBody.appendChild(tr);
  });

  var clsBody = document.querySelector("#classes-table tbody");
  tools.classes.forEach(function (row) {
    var tr = el("tr");
    tr.appendChild(el("td", null, row.cls));
    tr.appendChild(el("td", null, row.blurb));
    clsBody.appendChild(tr);
  });

  var mntBody = document.querySelector("#mounts-table tbody");
  tools.mounts.forEach(function (row) {
    var tr = el("tr");
    tr.appendChild(el("td", null, row.name));
    tr.appendChild(el("td", null, row.fastener));
    tr.appendChild(el("td", null, row.holes));
    tr.appendChild(el("td", null, row.origin));
    mntBody.appendChild(tr);
  });

  var rules = document.getElementById("rules-list");
  tools.rules.forEach(function (r) { rules.appendChild(el("li", null, r)); });

  var grid = document.getElementById("parts-grid");
  d.parts.forEach(function (p) {
    var card = el("div", "part-card");
    var img = document.createElement("img");
    img.src = p.svg;
    img.alt = "Preview of " + p.id;
    card.appendChild(img);
    var body = el("div", "part-body");
    body.appendChild(el("h3", null, p.id + " · " + p.title));
    body.appendChild(el("p", "meta", p.size + " · " + p.volume + " · " + p.status));
    var btn = el("button", "code-toggle", "Keel code");
    btn.type = "button";
    btn.addEventListener("click", function () { body.classList.toggle("open"); });
    body.appendChild(btn);
    var pre = el("pre", null, p.code);
    body.appendChild(pre);
    card.appendChild(body);
    grid.appendChild(card);
  });

  var reqBody = document.querySelector("#requests-table tbody");
  d.requests.forEach(function (r) {
    var tr = el("tr");
    tr.appendChild(el("td", null, r.id));
    tr.appendChild(el("td", null, r.title));
    tr.appendChild(el("td", null, r.request));
    var td = el("td");
    var cls = r.status.indexOf("Gauge PASS") === 0 ? "pass" : (r.status.indexOf("open") === 0 ? "open" : "draft");
    td.appendChild(el("span", "pill " + cls, r.status));
    tr.appendChild(td);
    reqBody.appendChild(tr);
  });

  document.getElementById("assistant-runs").textContent = d.assistant_panel.runs_on;

  var sb = document.getElementById("scoreboard");
  if (!d.assistant_panel.scoreboard) {
    sb.appendChild(el("p", "not-measured", "Not measured yet: no exam results on file."));
  } else {
    var t = el("table");
    d.assistant_panel.scoreboard_models.forEach(function (m) {
      var tr = el("tr");
      tr.appendChild(el("td", null, m));
      tr.appendChild(el("td", null, String(d.assistant_panel.scoreboard[m])));
      t.appendChild(tr);
    });
    sb.appendChild(t);
  }

  var trn = document.getElementById("training");
  var tstat = d.assistant_panel.training;
  trn.appendChild(el("p", null, "Status: " + tstat.status));
  trn.appendChild(el("p", null, "Cost: " + tstat.cost));
})();
