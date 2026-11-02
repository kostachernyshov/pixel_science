# Packs: the sprites (and the code that draws them) live in packs, not in the core.
#
#   packs/<name>/
#     pack.yaml      name, version, description, license
#     sprites/       PNG sheets, sprites.json, CREDITS.csv
#     code/          a Python package; code/library.py has build() -> sprites drawn in code
#
# Packs are found in <repo>/packs and in each folder of $PIXSCI_PACKS (separated by ":").
# A pack found later replaces one with the same name.

import importlib, importlib.util, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_found = None


class Pack:
    def __init__(self, path):
        import yaml
        self.dir = path
        self.meta = yaml.safe_load(open(os.path.join(path, "pack.yaml"), encoding="utf-8")) or {}
        self.name = self.meta.get("name") or os.path.basename(path)
        self.sprites_dir = os.path.join(path, "sprites")
        self._code = None

    def __repr__(self):
        return f"Pack({self.name!r})"

    def code(self):
        """The pack's code/library.py module (with build()), or None."""
        if self._code is None:
            init = os.path.join(self.dir, "code", "__init__.py")
            if not os.path.exists(init):
                self._code = False
            else:
                mod = "pixsci_pack_" + self.name.replace("-", "_")
                spec = importlib.util.spec_from_file_location(mod, init, submodule_search_locations=[os.path.dirname(init)])
                sys.modules[mod] = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sys.modules[mod])
                self._code = importlib.import_module(mod + ".library")
        return self._code or None


def search_path():
    return [os.path.join(ROOT, "packs")] + [p for p in os.environ.get("PIXSCI_PACKS", "").split(os.pathsep) if p]


def find():
    """{name: Pack} of every pack on the search path."""
    global _found
    if _found is None:
        _found = {}
        for root in search_path():
            if os.path.isdir(root):
                for d in sorted(os.listdir(root)):
                    if os.path.exists(os.path.join(root, d, "pack.yaml")):
                        p = Pack(os.path.join(root, d))
                        _found[p.name] = p
    return _found


def get(name):
    ps = find()
    if name not in ps:
        raise KeyError(f"unknown pack {name!r}; packs: {', '.join(sorted(ps))}")
    return ps[name]
