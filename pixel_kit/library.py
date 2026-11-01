# All sprites and animations of the library. tools/build_sprites.py builds
# sprites/*.png (frame = grid cell, row = animation) and sprites/sprites.json from here.
# A frame is a triple (Spr, dx, dy): dx, dy is the shift from the cell anchor (bob, lunge).

import math
from .palette import *
from .pixdraw import Spr, scale, silhouette, dominant, from_image
from . import cast as K
from . import props as PR
from . import people as PP
from . import office as OF

A = K.MHC_ANGLES


def F(s, dx=0, dy=0):
    return (s, dx, dy)


def anim(frames, fps=6, loop=True):
    return {"frames": frames, "fps": fps, "loop": loop}


# ---------------------------------------------------------------- common animations

def apoptosis(gen, rim=None):
    """Apoptosis, not an explosion: the cell closes its eyes, shrinks, buds off blebs
    (apoptotic bodies), and breaks into small fragments."""
    base = gen(blink=True)
    body = dominant(base, skip=(BLACK,))
    rim = rim if rim is not None else dominant(base.recolor({body: BLACK}), skip=(BLACK,))
    f2 = scale(base, 0.62)
    w = max(base.w, base.h) + 6
    blebs = Spr(w, w)
    c = w / 2
    for k in range(6):
        a = k * 1.05 + 0.3
        x, y = int(c + math.cos(a) * w * 0.36), int(c + math.sin(a) * w * 0.36)
        blebs.rect(x, y, x + 1, y + 1, body); blebs.put(x, y, rim)
    with_body = Spr(w, w)
    with_body.stamp(blebs, 0, 0)
    with_body.stamp(f2, (w - f2.w) // 2, (w - f2.h) // 2)
    frag = Spr(w + 4, w + 4)
    c2 = (w + 4) / 2
    for k in range(9):
        a = k * 0.72 + 0.1
        r = (w + 4) * (0.22 + 0.22 * ((k * 37) % 5) / 4)
        x, y = int(c2 + math.cos(a) * r), int(c2 + math.sin(a) * r)
        frag.put(x, y, body if k % 3 else rim)
    return anim([F(base), F(scale(base, 0.8)), F(with_body), F(frag)], fps=6, loop=False)


def division(gen):
    """Division: stretch, constriction, two daughter cells."""
    b = gen()
    st = scale(b, 1.2, 0.9)
    w = b.w
    two_close = Spr(int(w * 1.6) + 2, b.h)
    two_close.stamp(b, 0, 0); two_close.stamp(b, two_close.w - w, 0)
    two_far = Spr(int(w * 2.1) + 2, b.h)
    two_far.stamp(b, 0, 0); two_far.stamp(b, two_far.w - w, 0)
    return anim([F(b), F(st), F(two_close), F(two_far)], fps=5, loop=False)


def hit(gen):
    return anim([F(silhouette(gen(), NAVY)), F(gen())], fps=15, loop=False)


def idle(gen, fps=3):
    return anim([F(gen()), F(gen(), 0, -1)], fps=fps)


def move(gen):
    b = gen()
    return anim([F(b), F(scale(b, 1.1, 0.9), 0, 1), F(b, 0, -1)], fps=8)


def lunge(gen):
    a = gen(alert=True)
    return anim([F(a), F(scale(a, 1.15, 0.9), 2, 1), F(a, 1, 0), F(gen())], fps=10, loop=False)


def hero(gen, grey=True, extra=None):
    d = {
        "idle": idle(gen),
        "blink": anim([F(gen(blink=True))], fps=1),
        "move": move(gen),
        "alert": anim([F(gen(alert=True))], fps=1),
        "attack": lunge(gen),
        "hit": hit(gen),
        "death": apoptosis(gen),
    }
    if grey:
        d["blocked"] = anim([F(gen(grey=True)), F(gen(grey=True), 0, -1)], fps=1)
    d.update(extra or {})
    return d


def civilian(gen, divide=True, blink=True):
    d = {
        "idle": idle(gen, fps=2),
        "death": apoptosis(gen),
        "hit": hit(gen),
    }
    if blink:
        d["blink"] = anim([F(gen(blink=True))], fps=1)
    if divide:
        d["divide"] = division(gen)
    return d


# ---------------------------------------------------------------- tumor cells

def villain(angles=A, pdl1=(), stress=(), extra=None):
    def gen(blink=False, flash=False):
        return K.tumor(angles=angles, pdl1=pdl1, stress=stress, blink=blink, flash=flash)
    bare = lambda blink=False: K.tumor(angles=[], blink=blink)
    b = bare()
    two = Spr(b.w * 2 - 4, b.h)
    two.stamp(b, 0, 0); two.stamp(b, two.w - b.w, 0)
    d = {
        "idle": idle(gen),
        "blink": anim([F(gen(blink=True))], fps=1),
        "hit": anim([F(gen(flash=True)), F(gen())], fps=15, loop=False),
        "death": anim([F(K.tumor_apoptosis(k)) for k in range(4)], fps=6, loop=False),
        "divide": anim([F(gen()), F(scale(b, 1.2, 0.9)), F(K.tumor_dividing()), F(two)], fps=5, loop=False),
    }
    d.update(extra or {})
    return d


def _blast_gen(blink=False):
    return K.blast()


SPRITES = {}


def register(name, anims, group):
    SPRITES[name] = {"anims": anims, "group": group}


def build():
    SPRITES.clear()
    # immune cells
    register("nk", hero(lambda blink=False, alert=False, grey=False: K.nk(blink=blink, alert=alert, grey=grey)), "hero")
    for nm, kind in (("killer_t", "cd8"), ("helper_t", "cd4"), ("treg", "treg"), ("car_t", "cart")):
        register(nm, hero(lambda blink=False, alert=False, grey=False, kind=kind:
                          K.t_cell(kind, blink=blink, alert=alert, grey=grey)), "hero")
    register("b_cell", hero(lambda blink=False, alert=False: K.b_cell(blink=blink, alert=alert), grey=False), "hero")
    dc = lambda blink=False, alert=False, carry=True: K.dendritic(blink=blink, alert=alert, carry=carry)
    register("dendritic", hero(dc, grey=False, extra={
        "present": anim([F(dc(alert=True, carry=True)), F(dc(alert=True, carry=False))], fps=4)}), "hero")
    mg = lambda blink=False, alert=False, mouth=2: K.macrophage(blink=blink, alert=alert, mouth=mouth)
    rp = lambda blink=False, alert=False: K.macrophage(blink=blink, mode="repair")
    register("macrophage", hero(mg, grey=False, extra={
        "eat": anim([F(mg(alert=True, mouth=2)), F(mg(alert=True, mouth=1)), F(mg(mouth=0)), F(mg(mouth=0), 0, -1),
                     F(mg(mouth=1)), F(mg(mouth=2))], fps=8, loop=False),
        "repair": idle(rp, fps=2),
        "repair_blink": anim([F(rp(blink=True))], fps=1)}), "hero")
    # tumor cells
    register("tumor", villain(extra={
        "lose_mhc": anim([F(K.tumor(angles=K.keep_angles(n))) for n in range(8, 0, -1)] + [F(K.tumor(angles=[]))],
                         fps=4, loop=False)}), "villain")
    register("tumor_mhc_low", villain(angles=[A[1]]), "villain")
    register("tumor_no_mhc", villain(angles=[]), "villain")
    register("tumor_pdl1", villain(angles=A[::2], pdl1=A[1::2], extra={
        "pdl1_up": anim([F(K.tumor(angles=A[::2], pdl1=A[1::2][:k])) for k in range(5)], fps=4, loop=False)}), "villain")
    register("tumor_stress", villain(angles=A[::2], stress=[A[1], A[5]]), "villain")
    bl = lambda blink=False, alert=False: K.blast()
    gr = lambda blink=False: K.granulocyte(blink=blink)
    register("blast", {
        "idle": idle(bl), "hit": hit(bl),
        "death": anim([F(K.tumor_apoptosis(k)) for k in range(1, 4)], fps=6, loop=False),
        "mature": anim([F(K.blast()), F(silhouette(K.blast(), WHITE)), F(silhouette(gr(), WHITE)), F(gr()), F(gr(), 0, -1)],
                       fps=6, loop=False)}, "villain")
    # normal body cells
    register("epithelial", civilian(lambda blink=False: K.epithelial(blink)) | {
        "mutate": anim([F(K.epithelial()), F(silhouette(K.epithelial(), WHITE)), F(K.mutant()), F(K.mutant(), 0, -1)],
                       fps=6, loop=False)}, "civilian")
    register("stem", civilian(lambda blink=False: K.stem(blink)), "civilian")
    register("mutant", civilian(lambda blink=False: K.mutant(blink)), "civilian")
    for k in "ABCD":
        register("clone_" + k.lower(), civilian(lambda blink=False, k=k: K.clone(k, blink)), "civilian")
    register("senescent", civilian(lambda blink=False: K.senescent(), divide=False, blink=False), "civilian")
    register("granulocyte", civilian(lambda blink=False: K.granulocyte(blink), divide=False), "civilian")
    # badges
    for kind in ["mhc", "mhc_self", "mhc_neo", "tcr", "pd1", "ctla4", "pdl1", "stress"]:
        register("badge_" + kind, {"idle": anim([F(K.badge(kind))], fps=1)}, "badge")
    # props
    one = lambda s: {"idle": anim([F(s)], fps=1)}
    register("syringe", one(PR.syringe(BLUE)), "prop")
    register("syringe_drug", one(PR.syringe(ORANGE)), "prop")
    register("vial_antiserum", one(PR.vial(BLUE)), "prop")
    register("vial_drug", one(PR.vial(ORANGE)), "prop")
    register("dish", {"idle": anim([F(PR.dish(0))], fps=1),
                      "grow": anim([F(PR.dish(n)) for n in (1, 2, 4, 6)], fps=2, loop=False)}, "prop")
    register("mouse_top", one(PR.mouse_top()), "prop")
    register("mouse_side", {"idle": anim([F(PR.mouse_side()), F(PR.mouse_side(), 0, -1)], fps=3)}, "prop")
    register("dna", {"idle": anim([F(PR.dna())], fps=1), "mutate": anim([F(PR.dna()), F(PR.dna(True))], fps=3, loop=False)}, "prop")
    register("dna_mut", one(PR.dna(True)), "prop")
    register("glucose", one(PR.glucose()), "prop")
    register("pill", one(PR.pill()), "prop")
    register("granule_blue", {"idle": anim([F(PR.granule(BLUE, k)) for k in range(3)], fps=10)}, "prop")
    register("granule_green", {"idle": anim([F(PR.granule(GREEN, k)) for k in range(3)], fps=10)}, "prop")
    register("antibody", {"idle": anim([F(PR.antibody_bonus(0)), F(PR.antibody_bonus(1))], fps=4)}, "prop")
    register("chromosome", one(PR.chromosome()), "prop")
    register("chromosome_ph", one(PR.chromosome("ph")), "prop")
    # people and organs: three patients, no names
    for nm, hair, top in [("patient_a", "long", LAV), ("patient_b", "bob", PINK), ("patient_c", "short", BLUE)]:
        g = lambda hair=hair, top=top, **k: PP.person(hair, top, **k)
        register(nm, {
            "idle": anim([F(g()), F(g(), 0, -1)], fps=2),
            "blink": anim([F(g(blink=True))], fps=1),
            "sick": anim([F(g(sick=True)), F(g(sick=True), 0, 1)], fps=2),
            "gown": anim([F(g(gown=True)), F(g(gown=True), 0, -1)], fps=2),
            "gown_sick": anim([F(g(gown=True, sick=True)), F(g(gown=True, sick=True), 0, 1)], fps=2),
            "ghost": anim([F(g(ghost=True))], fps=1),
        }, "people")
    register("kidney", {
        "idle": anim([F(PP.kidney())], fps=1),
        "reveal": anim([F(PP.kidney(n)) for n in range(6)], fps=3, loop=False),
        "glow": anim([F(PP.kidney(5, glow=True)), F(PP.kidney(5))], fps=3),
    }, "prop")
    register("plaster", one(PP.ribbon()), "prop")
    # work world: people and objects, not cells
    mg_ = lambda **k: OF.manager(**k)
    register("manager", {
        "idle": anim([F(mg_()), F(mg_(), 0, -1)], fps=2),
        "blink": anim([F(mg_(blink=True))], fps=1),
        "panic": anim([F(mg_(arms="up")), F(mg_(arms="up"), 0, -1)], fps=6),
        "laptop": anim([F(mg_(laptop=True)), F(mg_(laptop=True), 0, -1)], fps=2),
    }, "people")
    sc_ = lambda **k: OF.scientist(**k)
    register("scientist", {
        "idle": anim([F(sc_()), F(sc_(), 0, -1)], fps=2),
        "blink": anim([F(sc_(blink=True))], fps=1),
        "panic": anim([F(sc_(arms="up")), F(sc_(arms="up"), 0, -1)], fps=6),
    }, "people")
    cl_ = lambda **k: OF.clinician(**k)
    register("clinician", {
        "idle": anim([F(cl_()), F(cl_(), 0, -1)], fps=2),
        "blink": anim([F(cl_(blink=True))], fps=1),
        "point": anim([F(cl_(arms="point")), F(cl_(arms="point"), 0, -1)], fps=2),
    }, "people")
    register("file_doc", one(OF.file_doc()), "prop")
    register("folder", one(OF.folder()), "prop")
    register("computer", {"idle": anim([F(OF.computer())], fps=1), "off": anim([F(OF.computer(False))], fps=1)}, "prop")
    register("check_card", one(OF.check_card()), "prop")
    yo = lambda **k: OF.person(**k)
    register("person", {
        "idle": anim([F(yo()), F(yo(), 0, -1)], fps=2),
        "blink": anim([F(yo(blink=True))], fps=1),
        "cheer": anim([F(yo(arms="up")), F(yo(arms="up"), 0, -1)], fps=6),
        "point": anim([F(yo(arms="point")), F(yo(arms="point"), 0, -1)], fps=2),
    }, "people")
    ag = lambda **k: OF.agent(**k)
    register("agent", {
        "idle": anim([F(ag()), F(ag(), 0, -1)], fps=2),
        "blink": anim([F(ag(blink=True))], fps=1),
        "work": anim([F(ag(work=k), 0, -(k % 2)) for k in (1, 2, 3)], fps=6),
        "alert": anim([F(ag(alert=True))], fps=1),
    }, "people")
    sv = lambda **k: OF.supervisor(**k)
    register("supervisor", {
        "idle": anim([F(sv()), F(sv(), 0, -1)], fps=2),
        "blink": anim([F(sv(blink=True))], fps=1),
        "alert": anim([F(sv(alert=True))], fps=1),
    }, "people")
    register("lock", {"idle": anim([F(OF.lock())], fps=1),
                      "open": anim([F(OF.lock()), F(OF.lock(True))], fps=4, loop=False)}, "prop")
    register("deck", one(OF.deck()), "prop")
    register("bulb", {"idle": anim([F(OF.bulb())], fps=1), "off": anim([F(OF.bulb(False))], fps=1),
                      "glow": anim([F(OF.bulb()), F(OF.bulb(False))], fps=3)}, "prop")
    # lab and data
    register("tube", one(PR.tube(BLUE)), "prop")
    register("tube_orange", one(PR.tube(ORANGE)), "prop")
    register("plate", {"idle": anim([F(PR.plate())], fps=1),
                       "fill": anim([F(PR.plate({(r, c): (XBLUE if c < 6 else ORANGE) for r in range(8) for c in range(k)}))
                                     for k in (0, 3, 6, 9, 12)], fps=3, loop=False)}, "prop")
    register("sequencer", {"idle": anim([F(PR.sequencer()), F(PR.sequencer(False))], fps=2),
                           "off": anim([F(PR.sequencer(False))], fps=1)}, "prop")
    register("datasheet", one(PR.datasheet()), "prop")
    return SPRITES
