"""Free retrieval-coverage audit for Option A (prototype, 2026-10-29, Claude).

Question (user's noon gate): for each of the 30 exam jobs, do the top-5 past designs retrieved by plain BM25 (no
programme/family bonus, verifier drafts fix 1) contain every hidden-rule instance the job needs?
The official library does not exist yet, so this builds a PROTOTYPE library of request texts + rule-instance tags from
the coverage targets in HIDDEN_STANDARDS.DRAFT.md (Tern 110, Skua 110, no programme 80; >= 8 per threshold side per
programme; >= 3 exactly at each threshold edge; overrides). Programs are not generated: the audit needs only the
request text (what retrieval sees) and which rules each design shows. Result = a prediction for the real library.
Run: python coverage_audit.py [--seeds 5] [--k 5]
"""
import argparse, math, random, re, sys
from collections import Counter

FAMS = ["BRK", "PLT", "FRM", "CLP", "STD"]
FAMNAME = {"BRK": "bracket", "PLT": "plate", "FRM": "frame", "CLP": "clip", "STD": "standoff"}
MATNAME = {"AL6061": "aluminium", "TI6AL4V": "titanium", "SS316": "stainless"}


def tok(s):  # frozen tokenisation: lowercase, alphanumeric runs, numbers kept
    return re.findall(r"[a-z0-9]+", s.lower())


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [tok(d) for d in docs]
        self.N = len(docs); self.avg = sum(map(len, self.docs)) / self.N
        df = Counter(t for d in self.docs for t in set(d))
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()}
        self.tf = [Counter(d) for d in self.docs]; self.k1, self.b = k1, b

    def top(self, q, k):
        qt = tok(q); sc = []
        for i, (tf, d) in enumerate(zip(self.tf, self.docs)):
            s = 0.0
            for t in qt:
                if t in tf:
                    f = tf[t]; s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            sc.append((-s, i))
        return [i for _, i in sorted(sc)[:k]]


def design(rng, num, prog, fam, force=None):
    """Return (request_text, set_of_rule_instances). force: dict of attributes to pin (threshold quotas)."""
    f = dict(force or {})
    inst = set()
    words = [f"{fam}-{num}"] + ([prog.capitalize()] if prog else []) + [FAMNAME[fam]]
    mat = None; flight = False
    if prog == "skua":
        if f.get("mat_ovr") or rng.random() < 0.12:
            mat = rng.choice(["AL6061", "SS316"]); inst.add("MAT_OVR_SKUA")
        else:
            inst.add("TI_DEF")
        if f.get("gse") or rng.random() < 0.07:
            inst.add("GSE_SKUA"); flight = False
        else:
            inst.add("FLT_SKUA"); flight = True
        inst.add("FIL_SKUA")
    elif prog == "tern":
        if rng.random() < 0.5:
            mat = rng.choice(["AL6061", "TI6AL4V", "SS316"])
        flight = f.get("flight", rng.random() < 0.4)
    else:
        if rng.random() < 0.5:
            mat = rng.choice(["AL6061", "TI6AL4V", "SS316"])
        flight = rng.random() < 0.3
    tail = []
    if mat: tail.append(MATNAME[mat])
    if prog == "skua" and "GSE_SKUA" in inst: tail.append("ground-support part (GSE, not a flight part)")
    elif prog != "skua" and flight: tail.append("flight part")
    head = " ".join(words) + (", " + ", ".join(tail) if tail else "") + "."
    body = []
    walls = []
    if fam == "BRK":
        L = f.get("L", rng.choice(range(50, 90, 2)))
        W = rng.choice(range(30, 64, 2)); T = rng.choice([6, 8]) if prog == "skua" else rng.choice([4, 5, 6, 8])
        n = 2 if rng.random() < 0.25 else 1
        edges = rng.sample(["north", "south", "east", "west"], n)
        for e in edges:
            h = f.get("h", rng.choice(range(10, 31, 1)))
            walls.append((e, h)); f.pop("h", None)
        body.append(f"Stock {L} x {W} x {T}, " + " and ".join(f"a wall on the {e} edge, {h} high" for e, h in walls) + ".")
        if prog:
            inst.add(f"BRK_{prog.upper()}"); inst.add(f"WH_{prog.upper()}")
            if L >= 90: inst.add("BRK_LONG")
            if f.get("size_ovr") or rng.random() < 0.08:
                body.append(f"The corner holes are KF-M{rng.choice([3, 6])}."); inst.add("BRK_SIZE_OVR")
        else:
            body.append(f"Four KF-M4 holes {rng.choice([5, 6, 8])} mm in from each corner.")
    elif fam == "PLT":
        L = rng.choice(range(80, 160, 5)); W = rng.choice(range(60, 110, 5)); T = rng.choice([4, 5, 6])
        body.append(f"Stock {L} x {W} x {T}.")
        if rng.random() < 0.5: body.append(f"One KF-M{rng.choice([3, 4, 6])} hole with its centre at ({L - 12}, {W - 12}).")
        if prog: inst.add(f"PLT_{prog.upper()}")
        else: body.append(f"A PETREL-MOUNT-{rng.choice('AB')} with its south-west hole at ({rng.choice([10, 15, 20])}, {rng.choice([10, 15])}).")
        if prog and rng.random() < 0.25:
            body.append("Two HARNESS-P2 mounts along the north side."); inst.add("HAS_M2")
    elif fam == "FRM":
        L = rng.choice(range(80, 140, 5)); W = rng.choice(range(60, 110, 5)); T = rng.choice([6, 8, 10])
        a, b = L // 2 - rng.choice([6, 7, 8]), W // 2 - rng.choice([6, 7, 8])
        body.append(f"Stock {L} x {W} x {T}. Four KF-M{rng.choice([4, 5])} holes at (-{a}, -{b}), ({a}, -{b}), (-{a}, {b}) and ({a}, {b}).")
        if rng.random() < 0.35:
            h = f.get("h", rng.choice(range(10, 31)))
            walls = [("north", h), ("south", h)]; body.append(f"Walls on the north and south edges, each {h} high.")
        if prog: inst.add(f"FRM_{prog.upper()}")
        else: body.append(f"A pocket {L - 20} x {W - 20}, {T // 2} deep, centred.")
    elif fam == "CLP":
        L = f.get("L", rng.choice(range(40, 60, 2))); W = rng.choice(range(20, 34, 2)); T = rng.choice([4, 5])
        body.append(f"Stock {L} x {W} x {T}.")
        if rng.random() < 0.5:
            h = f.get("h", rng.choice(range(10, 21))); e = rng.choice(["east", "west"]); walls = [(e, h)]
            body.append(f"A wall on the {e} edge, {h} high.")
        if prog:
            inst.add("CLP"); inst.add("HAS_M2")
            if L >= 60: inst.add("CLP_LONG")
        else: body.append(f"A HARNESS-P2 mount with its west hole at (8, {W // 2}).")
    else:  # STD
        a = rng.choice(range(28, 52, 2)); d = rng.choice([10, 12, 14, 16]); h = rng.choice(range(8, 22, 2))
        body.append(f"Foot {a} x {a} x {rng.choice([4, 5, 6])} with a boss of diameter {d}, {h} high, centred on the foot.")
        if prog:
            inst.add("STD")
            if rng.random() < 0.12: body.append("The boss hole is a countersunk KF-M5."); inst.add("STD_OVR")
        else: body.append("A KF-M4 hole through the boss.")
    if prog == "skua" and walls: inst.add("T4_SKUA")
    if prog == "tern" and walls:
        if any(h > 30 for _, h in walls): inst.add("TALL_TERN")
    if prog and flight:
        inst.add("CB_FLT")
        if "HAS_M2" in inst: inst.add("CS_M2")
    inst.discard("HAS_M2")
    return head + " " + " ".join(body), inst


def library(seed):
    rng = random.Random(seed); out = []; num = iter(range(8000, 9999))
    for prog, n in (("tern", 110), ("skua", 110), (None, 80)):
        per = {fm: n // 5 for fm in FAMS}
        for fm in FAMS:
            forces = []
            if prog and fm == "BRK":
                forces += [{"L": 90}] * 3 + [{"L": rng.choice(range(92, 122, 2))} for _ in range(5)]
                forces += [{"size_ovr": True}] * 2
                if prog == "tern": forces += [{"h": 30}] * 3 + [{"h": rng.choice(range(32, 50))} for _ in range(5)]
                if prog == "skua": forces += [{"mat_ovr": True}] * 2 + [{"gse": True}]
            if prog and fm == "CLP":
                forces += [{"L": 60}] * 3 + [{"L": rng.choice(range(62, 92, 2))} for _ in range(5)]
            if prog == "tern" and fm == "FRM":
                forces += [{"h": rng.choice(range(32, 46))} for _ in range(3)]
            if prog == "skua" and fm in ("PLT", "STD"):
                forces += [{"mat_ovr": True}, {"gse": True}]
            for i in range(per[fm]):
                out.append(design(rng, next(num), prog, fm, forces[i] if i < len(forces) else None))
    return out


EXAM_NEEDS = {  # rule instances each exam job needs (from jobs.DRAFT.py refs)
    "M1": "BRK_TERN WH_TERN", "M2": "TI_DEF FLT_SKUA CB_FLT T4_SKUA FIL_SKUA BRK_SKUA WH_SKUA",
    "M3": "PLT_TERN", "M4": "TI_DEF FLT_SKUA CB_FLT FIL_SKUA PLT_SKUA", "M5": "CLP",
    "M6": "TI_DEF FLT_SKUA CS_M2 FIL_SKUA CLP", "M7": "FRM_TERN", "M8": "TI_DEF FLT_SKUA CB_FLT FIL_SKUA FRM_SKUA",
    "M9": "STD", "M10": "TI_DEF FLT_SKUA CB_FLT FIL_SKUA STD", "M11": "CB_FLT BRK_TERN WH_TERN",
    "M12": "CB_FLT PLT_TERN", "M13": "MAT_OVR_SKUA FLT_SKUA CB_FLT T4_SKUA FIL_SKUA BRK_SKUA WH_SKUA",
    "M14": "CLP CLP_LONG", "M15": "FRM_TERN",
    "H1": "TI_DEF FLT_SKUA CB_FLT T4_SKUA FIL_SKUA BRK_SKUA BRK_LONG WH_SKUA", "H2": "TALL_TERN BRK_TERN WH_TERN",
    "H3": "CB_FLT BRK_TERN BRK_LONG WH_TERN", "H4": "TI_DEF FLT_SKUA CB_FLT FIL_SKUA PLT_SKUA",
    "H5": "MAT_OVR_SKUA FLT_SKUA CS_M2 CB_FLT FIL_SKUA CLP CLP_LONG",
    "H6": "TI_DEF FLT_SKUA CB_FLT T4_SKUA FIL_SKUA FRM_SKUA", "H7": "CB_FLT FRM_TERN",
    "H8": "MAT_OVR_SKUA FLT_SKUA CB_FLT FIL_SKUA STD STD_OVR", "H9": "CB_FLT STD", "H10": "CB_FLT CS_M2 PLT_TERN",
    "H11": "TI_DEF FLT_SKUA CB_FLT T4_SKUA FIL_SKUA BRK_SKUA BRK_SIZE_OVR WH_SKUA",
    "H12": "CB_FLT TALL_TERN BRK_TERN BRK_LONG WH_TERN", "H13": "TI_DEF FLT_SKUA CS_M2 T4_SKUA FIL_SKUA CLP",
    "H14": "TALL_TERN FRM_TERN", "H15": "TI_DEF GSE_SKUA FIL_SKUA PLT_SKUA",
}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=5); ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--verbose", action="store_true"); a = ap.parse_args()
    sys.path.insert(0, __file__.rsplit("/audit/", 1)[0])
    from jobs_draft import JOBS
    rates, missing_all = [], Counter()
    for seed in range(a.seeds):
        lib = library(seed); bm = BM25([t for t, _ in lib]); full = 0
        for jid, job in JOBS.items():
            need = set(EXAM_NEEDS[jid].split())
            seen = set().union(*(lib[i][1] for i in bm.top(job["text"], a.k)))
            miss = need - seen
            if not miss: full += 1
            else: missing_all.update(miss)
            if a.verbose and seed == 0: print(jid, "OK" if not miss else f"MISS {sorted(miss)}")
        rates.append(full / len(JOBS))
    print(f"library size {len(lib)}; k={a.k}; seeds={a.seeds}")
    print("fully covered jobs per seed:", [f"{r:.0%}" for r in rates], f"mean {sum(rates) / len(rates):.0%}")
    print("most-missed instances (all seeds):", missing_all.most_common(8))


if __name__ == "__main__":
    main()
