# Packs: everything the core draws comes from a pack. The core knows no pack by name.
#
# A pack is a folder with pack.yaml. It can provide:
#   sprites/      PNG sheets, sprites.json (cells, animations, tags), CREDITS.csv
#   code/         a Python package; code/library.py has build() -> sprites drawn in code
#   backgrounds.py  functions name(t) -> PIL image of frame.W x frame.H, listed in BACKGROUNDS
#   style:        (in pack.yaml) a style: palette, roles, filters, sprite parameters (see style.py)
#   bible.md      roles and colors of the characters
#   examples/     example plans
#
#   from pixel_kit import packs
#   packs.find()                       {name: Pack} of all packs on the search path
#   packs.get("biology")
#   packs.stack(["biology", "physics"])   bottom -> top; a higher pack overrides a lower one
#
# Search path: <repo>/packs, then each folder in $PIXSCI_PACKS (separated by ":").
# A pack in a later folder replaces a pack with the same name in an earlier one.

import csv, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS_DIR = os.path.join(ROOT, "packs")
_found = None


class PackError(Exception):
    pass


class Pack:
    def __init__(self, path):
        import yaml
        self.dir = path
        self.meta = yaml.safe_load(open(os.path.join(path, "pack.yaml"), encoding="utf-8")) or {}
        self.name = self.meta.get("name") or os.path.basename(path)
        self.kind = self.meta.get("kind", "content")
        self._sprites = None
        self._credits = None
        self._code = None
        self._bgs = None
        self.bg_animated = set()
        self.bg_tags = {}

    def __repr__(self):
        return f"Pack({self.name!r}, {self.kind})"

    @property
    def description(self):
        return self.meta.get("description", "")

    @property
    def sprites_dir(self):
        return os.path.join(self.dir, self.meta.get("sprites", "sprites"))

    def sprites(self):
        """{name: meta} from sprites/sprites.json (empty if the pack has no sprites)."""
        if self._sprites is None:
            p = os.path.join(self.sprites_dir, "sprites.json")
            self._sprites = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        return self._sprites

    def credits(self):
        if self._credits is None:
            p = os.path.join(self.sprites_dir, "CREDITS.csv")
            self._credits = ({r["sprite"]: r for r in csv.DictReader(open(p, encoding="utf-8"))}
                             if os.path.exists(p) else {})
        return self._credits

    def code(self):
        """The pack's code package (code/__init__.py), or None. Its library.build() draws sprites."""
        if self._code is None:
            init = os.path.join(self.dir, "code", "__init__.py")
            if not os.path.exists(init):
                self._code = False
            else:
                modname = "pixsci_pack_" + self.name.replace("-", "_")
                spec = importlib.util.spec_from_file_location(
                    modname, init, submodule_search_locations=[os.path.dirname(init)])
                mod = importlib.util.module_from_spec(spec)
                sys.modules[modname] = mod
                spec.loader.exec_module(mod)
                lib = importlib.import_module(modname + ".library")
                self._code = lib
        return self._code or None

    def backgrounds(self):
        """{name: fn(t)} from backgrounds.py (BACKGROUNDS dict)."""
        if self._bgs is None:
            p = os.path.join(self.dir, "backgrounds.py")
            self._bgs = {}
            if os.path.exists(p):
                spec = importlib.util.spec_from_file_location("pixsci_bg_" + self.name.replace("-", "_"), p)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self._bgs = dict(getattr(mod, "BACKGROUNDS", {}))
                self.bg_animated = set(getattr(mod, "ANIMATED", ()))
                self.bg_tags = dict(getattr(mod, "TAGS", {}))
        return self._bgs

    @property
    def style(self):
        return self.meta.get("style")

    @property
    def bible(self):
        p = os.path.join(self.dir, "bible.md")
        return p if os.path.exists(p) else None


def search_path():
    extra = [p for p in os.environ.get("PIXSCI_PACKS", "").split(os.pathsep) if p]
    return [PACKS_DIR] + extra


def find(refresh=False):
    global _found
    if _found is None or refresh:
        _found = {}
        for root in search_path():
            if not os.path.isdir(root):
                continue
            for d in sorted(os.listdir(root)):
                p = os.path.join(root, d)
                if os.path.exists(os.path.join(p, "pack.yaml")):
                    pk = Pack(p)
                    _found[pk.name] = pk
    return _found


def get(name):
    ps = find()
    if name not in ps:
        raise PackError(f"unknown pack {name!r}; packs: {', '.join(sorted(ps))}")
    return ps[name]


def content():
    return [p for p in find().values() if p.kind == "content"]


def styles():
    """{style name: Pack} for each style pack."""
    return {p.style["name"]: p for p in find().values() if p.kind == "style" and p.style}


def stack(names):
    """Content packs bottom -> top. Unknown names raise PackError."""
    out = []
    for n in names:
        p = get(n)
        if p.kind != "content":
            raise PackError(f"pack {n!r} is a {p.kind} pack; set it with 'style:', not 'packs:'")
        out.append(p)
    return out
