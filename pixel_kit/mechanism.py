# The mechanism model of a video, and the drawing rules every scene must keep.
#
# A plan names what takes part in its story and how, with a source for each link. No global table of
# who binds whom: the agent writes only the 3 to 6 links of this story, from its sources.
#
#   model:
#     things:                                 # bodies on screen; parts sit on their surface
#       t:     {sprite: killer_t, label: "KILLER T CELL",
#               parts: {tcr: {label: TCR, color: GREEN}, pd1: {label: PD-1, color: LGREY}}}
#       tumor: {sprite: tumor_pdl1, label: "TUMOR CELL",
#               parts: {mhc1: {label: MHC-I, color: YELLOW}, pdl1: {label: PD-L1, color: PINK}}}
#       drug:  {label: "ANTI-PD-L1", color: BLUE}          # a free agent: no body, it travels
#     links:                                  # each one cites a source (its number in sources:)
#       signal: {kind: bind,   a: tcr,  b: mhc1,  source: 1}
#       brake:  {kind: bind,   a: pd1,  b: pdl1,  source: 1}
#       block:  {kind: occupy, a: drug, b: pdl1,  source: 4}
#       kill:   {kind: kill,   a: t,    b: tumor, source: 3}
#
# Link kinds are verbs that fit any science:
#   bind    two parts on two bodies touch and hold (receptor-ligand, a key in a lock, two plates locked)
#   occupy  a free agent sits on a part; the part lets go of its other binds (a drug on a receptor, a
#           poison on an enzyme)
#   kill    a ends b (apoptosis, a decay, a collapse); b plays its death animation and stays dead
#
# The rules (pixsci check enforces them):
#   scale       a link between parts is drawn in a contact scene, where the parts are visible objects
#   contact     a bind is drawn only between parts on the two bodies of the scene, where they meet
#   ownership   a part sits on the surface of its own body; a body shows only its own parts
#   specificity an agent occupies only the part its link names
#   persistence the state carries from scene to scene: what is bound stays bound, what is dead stays
#               dead, until a link changes it; a scene starts where the last one ended
#   causality   a link is undone only after it was done
#   sourced     every link cites a source, and every link of the model is shown in some scene
#
# Shapes come from the links, not from a table: each bind link gets a profile (PROFILES) from its name, the a part
# gets a socket of that profile and the b part a key of the same profile, so partners fit and other
# parts do not. An occupying agent gets the partner's shape: it visibly takes the same place.

import zlib

KINDS = ("bind", "occupy", "kill")
ROWS = 7


def model(plan):
    m = plan.get("model") or {}
    return m.get("things") or {}, m.get("links") or {}


def parts(plan):
    """{part: (thing, meta)}"""
    things, _ = model(plan)
    out = {}
    for th, d in things.items():
        for p, pm in (d.get("parts") or {}).items():
            out[p] = (th, pm or {})
    return out


# Site profiles: socket depths (0..3) for the 7 rows of a head. Each reads at a glance and differs from the
# others; the links of a plan get different ones, so in one video no two sites look alike.
PROFILES = [
    [0, 3, 3, 3, 3, 3, 0],      # cup
    [0, 1, 2, 3, 2, 1, 0],      # wedge
    [0, 3, 3, 0, 3, 3, 0],      # double
    [0, 0, 3, 3, 3, 0, 0],      # step
    [3, 2, 1, 0, 1, 2, 3],      # vee
    [0, 0, 0, 3, 0, 0, 0],      # slot
    [3, 3, 0, 0, 0, 3, 3],      # fork
]


def profile(plan, link_name):
    """The site profile of a bind link: chosen from its name, unique within the plan."""
    _, links = model(plan)
    used = {}
    for name, l in links.items():
        if l.get("kind") != "bind":
            continue
        i = zlib.crc32(name.encode()) % len(PROFILES)
        while i in used.values() and len(used) < len(PROFILES):
            i = (i + 1) % len(PROFILES)
        used[name] = i
    return PROFILES[used.get(link_name, zlib.crc32(link_name.encode()) % len(PROFILES))]


def site(plan, part):
    """(link name, role "a"/"b") of the first bind link of a part: it sets the part's shape."""
    _, links = model(plan)
    for name, l in links.items():
        if l.get("kind") == "bind" and part in (l.get("a"), l.get("b")):
            return name, "a" if l["a"] == part else "b"
    return None, None


def cells(prof, role):
    """Head cells (col, row) for a role; col 0 is at the stalk, cols grow toward the partner.
    a: a block 4 wide with a socket of the profile's depths; b: a base 2 wide and a key of the same depths."""
    if role == "a":
        return [(c, r) for r in range(ROWS) for c in range(4 - prof[r])]
    return [(c, r) for r in range(ROWS) for c in range(2 + prof[r])]


def shape(plan, name):
    """Head cells of a part or of an occupying agent."""
    _, links = model(plan)
    if name in parts(plan):
        ln, role = site(plan, name)
        return cells(profile(plan, ln), role) if ln else cells([0, 0, 1, 1, 1, 0, 0], "b")
    for ln, l in links.items():
        if l.get("kind") == "occupy" and l.get("a") == name:
            sl, role = site(plan, l["b"])
            prof = profile(plan, sl) if sl else [0, 0, 1, 1, 1, 0, 0]
            return cells(prof, "a" if role == "b" else "b")
    return cells([0, 0, 1, 1, 1, 0, 0], "b")


# ---------------------------------------------------------------- the world, scene by scene

def world(plan):
    """The state at the start of each scene: [{"on": set of active links, "dead": set of things}].
    Contact scenes change it with do/undo beats; a death animation of an actor kills it too."""
    _, links = model(plan)
    on, dead, out = set(), set(), []
    for sc in plan["scenes"]:
        out.append({"on": set(on), "dead": set(dead)})
        for b in sorted(sc.get("beats") or [], key=lambda b: (b.get("_t", 0.0), str(b.get("on", "")))):
            if "do" in b and b["do"] in links:
                l = links[b["do"]]
                on.add(b["do"])
                if l.get("kind") == "occupy":
                    for n2, l2 in links.items():          # the occupied part lets go of its binds
                        if l2.get("kind") == "bind" and l["b"] in (l2.get("a"), l2.get("b")):
                            on.discard(n2)
                if l.get("kind") == "kill":
                    dead.add(l["b"])
            if "undo" in b:
                on.discard(b["undo"])
            if b.get("anim") == "death":
                who = b.get("actor") or (sc.get(b.get("cell")) if b.get("cell") in ("left", "right") else None)
                if isinstance(who, str):
                    dead.add(who)
        for name, a in (sc.get("actors") or {}).items():
            if a.get("anim") == "death":
                dead.add(name)
    return out


# ---------------------------------------------------------------- checks

def check(plan):
    things, links = model(plan)
    contact = [sc for sc in plan["scenes"] if sc.get("type") == "contact"]
    if not contact and not links:
        return []
    out = []
    if contact and not links:
        return ["contact scenes need 'model:' with things and links (see pixel_kit/mechanism.py)"]
    P = parts(plan)
    nsrc = len(plan.get("sources") or [])
    for name, l in links.items():
        k, a, b = l.get("kind"), l.get("a"), l.get("b")
        tag = f"model link {name}"
        if k not in KINDS:
            out.append(f"{tag}: kind must be one of {', '.join(KINDS)}")
            continue
        src = l.get("source")
        if not isinstance(src, int) or not 1 <= src <= nsrc:
            out.append(f"{tag}: source must be the number of a source in 'sources:' (1..{nsrc})")
        if k == "bind":
            for x in (a, b):
                if x not in P:
                    out.append(f"{tag}: {x!r} is not a part of a thing (things: ... parts:)")
            if a in P and b in P and P[a][0] == P[b][0]:
                out.append(f"{tag}: {a} and {b} sit on the same body; a bind joins parts of two bodies")
        elif k == "occupy":
            if a not in things or things[a].get("parts"):
                out.append(f"{tag}: {a!r} must be a free agent in things (no parts)")
            if b not in P:
                out.append(f"{tag}: {b!r} is not a part of a thing")
        elif k == "kill":
            for x in (a, b):
                if x not in things:
                    out.append(f"{tag}: {x!r} is not a thing")
    if out:
        return out
    shown = set()
    states = world(plan)
    for sc, st in zip(plan["scenes"], states):
        sid = sc.get("id", "?")
        if sc.get("type") == "action":
            for name, a in (sc.get("actors") or {}).items():
                if name in st["dead"] and a.get("anim") != "death" and a.get("show") is not False:
                    out.append(f"{sid}: actor {name!r} died in an earlier scene and cannot come back")
            continue
        if sc.get("type") != "contact":
            continue
        L, R = sc.get("left"), sc.get("right")
        for side, x in (("left", L), ("right", R)):
            if x not in things or not things[x].get("sprite"):
                out.append(f"{sid}: {side} must be a thing of the model with a sprite")
            elif x in st["dead"]:
                out.append(f"{sid}: {x!r} died in an earlier scene and cannot come back")
        if out and out[-1].startswith(sid):
            continue
        rows = rows_of(plan, sc)
        for ln in sc.get("show") or []:
            l = links.get(ln)
            if not l or l.get("kind") != "bind":
                out.append(f"{sid}: show: {ln!r} is not a bind link of the model")
            elif {P[l['a']][0], P[l['b']][0]} != {L, R}:
                out.append(f"{sid}: show: {ln} joins parts of {P[l['a']][0]} and {P[l['b']][0]}, "
                           f"not of {L} and {R} (contact)")
        on = set(st["on"])
        row_parts = {p for ln in rows for p in (links[ln]["a"], links[ln]["b"])}
        for b in sorted(sc.get("beats") or [], key=lambda b: b.get("_t", 0.0)):
            if b.get("cell") and b["cell"] not in ("left", "right"):
                out.append(f"{sid}: beat cell must be left or right, not {b['cell']!r}")
            if b.get("actor"):
                out.append(f"{sid}: a contact scene has cells (cell: left/right), not actors")
            if "do" in b:
                ln = b["do"]
                l = links.get(ln)
                if not l:
                    out.append(f"{sid}: do: {ln!r} is not a link of the model ({', '.join(links)})")
                    continue
                shown.add(ln)
                if l["kind"] == "bind" and ln not in rows:
                    out.append(f"{sid}: do: {ln} binds parts that are not on {L} and {R} (contact)")
                if l["kind"] == "occupy" and l["b"] not in row_parts:
                    out.append(f"{sid}: do: {ln}: {l['b']} is not shown in the scene (specificity)")
                if l["kind"] == "kill" and {l["a"], l["b"]} != {L, R}:
                    out.append(f"{sid}: do: {ln}: {l['a']} kills {l['b']}, who are not the cells of the scene")
                on.add(ln)
            if "undo" in b:
                if b["undo"] not in on:
                    out.append(f"{sid}: undo: {b['undo']!r} is not active here (causality)")
                on.discard(b["undo"])
        shown |= {ln for ln in st["on"] if ln in rows}
    for ln in links:
        if ln not in shown:
            out.append(f"model link {ln}: no scene shows it (do: {ln} in a contact scene)")
    return out


def rows_of(plan, sc):
    """The bind links drawn as rows in a contact scene: 'show', or every bind between parts of left and right."""
    _, links = model(plan)
    if sc.get("show"):
        return [ln for ln in sc["show"] if ln in links]
    P = parts(plan)
    L, R = sc.get("left"), sc.get("right")
    return [ln for ln, l in links.items() if l.get("kind") == "bind" and l["a"] in P and l["b"] in P
            and {P[l["a"]][0], P[l["b"]][0]} == {L, R}]
