# Storyboards: the key frame of each scene with its time and voice-over text.
#
#   board.png_board(plan, "out/board-landscape.png")      one format, the active style
#   board.html_board(plan, "out/board.html", formats, styles)   one self-contained page: a format
#       switch, a style switch, the text to read under each frame, sources and warnings.
#       An agent that can publish artifacts shows this page to the person; else it shows the PNGs.

import base64, html, io, json, os
from PIL import Image
from . import frame, style, explain
from .font import text


def _tiles(plan, k=2):
    tl, marks = explain.timeline(plan)
    out = []
    for t, label in marks:
        im = Image.fromarray(tl.frame(t))
        out.append((im.resize((frame.W * k, frame.H * k), Image.NEAREST), t, label))
    return out


def png_board(plan, path, cols=None, gap=12):
    tiles = _tiles(plan)
    cols = cols or (3 if frame.W >= frame.H else 4)
    tw, th = tiles[0][0].size
    lab_h = 20
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + gap) + gap, rows * (th + gap + lab_h) + gap), (220, 212, 206))
    with style.base():
        from .palette import INK
        for i, (im, t, label) in enumerate(tiles):
            x, y = gap + (i % cols) * (tw + gap), gap + (i // cols) * (th + gap + lab_h)
            sheet.paste(im, (x, y))
            text(sheet, x + 4, y + th + 2, label.split()[0] + f"  {t:.1f} s", INK)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sheet.save(path)
    return path


def _b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def html_board(plan, path, formats, styles, warnings=()):
    vo = explain.voiceover(plan)
    tm = explain.timing(plan)
    images = {}
    for st in styles:
        explain.prepare(plan, st)
        for f in formats:
            frame.use(f)
            images[f"{st}/{f}"] = [_b64(im) for im, _, _ in _tiles(plan, k=2)]
    explain.prepare(plan)
    scenes = []
    for sc, s in zip(plan["scenes"], tm):
        scenes.append({"id": sc.get("id"), "type": sc.get("type"), "start": round(s["start"], 1),
                       "end": round(s["end"], 1), "caption": sc.get("caption") or "",
                       "text": vo.get(sc.get("id"), "")})
    data = {"title": plan.get("title", ""), "formats": formats, "styles": styles,
            "style": plan.get("style", "paper"), "scenes": scenes, "images": images,
            "sources": plan.get("sources") or [], "warnings": list(warnings),
            "length": round(tm[-1]["end"], 1) if tm else 0}
    short = (plan.get("title") or plan.get("name") or "Video").split(":")[0].strip()
    page = TEMPLATE.replace("__NAME__", html.escape(short + " storyboard")) \
                   .replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path


TEMPLATE = """<title>__NAME__</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@500&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
/* Layout: a contact sheet of key frames, one card per scene, the voice-over under each frame. */
:root {
  --bg: #f4f2ee; --card: #ffffff; --ink: #1d2b53; --muted: #5f574f; --line: #e1ddd6;
  --warn-bg: #fff1dc; --warn-ink: #6e4300; --chip: #e9e5de; --chip-on: #1d2b53; --chip-on-ink: #ffffff;
  --display: "Pixelify Sans", ui-monospace, "SF Mono", Menlo, monospace;
  --body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #12111a; --card: #1c1b26; --ink: #f2eee8; --muted: #a8a2b8; --line: #2e2c3c;
    --warn-bg: #3a2a10; --warn-ink: #ffd28a; --chip: #2a2838; --chip-on: #29adff; --chip-on-ink: #0a0814;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #12111a; --card: #1c1b26; --ink: #f2eee8; --muted: #a8a2b8; --line: #2e2c3c;
  --warn-bg: #3a2a10; --warn-ink: #ffd28a; --chip: #2a2838; --chip-on: #29adff; --chip-on-ink: #0a0814;
  color-scheme: dark;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 var(--body); }
main { max-width: 1180px; margin: 0 auto; padding-block: 24px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
h1 { font: 500 26px/1.2 var(--display); margin: 0 0 6px; text-wrap: balance; }
.meta { color: var(--muted); margin: 0 0 16px; }
.bar { display: flex; flex-wrap: wrap; gap: 12px 20px; margin: 0 0 16px; align-items: center; }
.group { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.group span { color: var(--muted); font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; margin-right: 2px; }
button { border: 0; border-radius: 6px; padding: 6px 12px; background: var(--chip); color: var(--ink); font: inherit; font-size: 14px; cursor: pointer; }
button:focus-visible { outline: 2px solid var(--chip-on); outline-offset: 2px; }
button[aria-pressed="true"] { background: var(--chip-on); color: var(--chip-on-ink); }
.warn { background: var(--warn-bg); color: var(--warn-ink); border-radius: 8px; padding: 10px 14px; margin: 0 0 16px; }
.warn ul { margin: 4px 0 0; padding-left: 18px; }
.grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(min(100%, var(--min)), 1fr)); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; min-width: 0; }
.card img { width: 100%; max-width: 100%; display: block; image-rendering: pixelated; }
.body { padding: 10px 12px 12px; display: grid; gap: 2px; }
.head { display: flex; justify-content: space-between; gap: 8px; color: var(--muted); font-size: 13px; font-variant-numeric: tabular-nums; }
.head b { color: var(--ink); font-family: var(--display); font-weight: 500; }
.cap { font-weight: 600; }
.say { margin: 0; }
footer { margin-top: 28px; color: var(--muted); font-size: 13px; }
footer ol { padding-left: 18px; }
</style>
<main>
  <h1 id="title"></h1>
  <p class="meta" id="meta"></p>
  <div class="bar">
    <div class="group" id="formats"><span>Format</span></div>
    <div class="group" id="styles"><span>Style</span></div>
  </div>
  <div id="warn"></div>
  <div class="grid" id="grid"></div>
  <footer><b>Sources</b><ol id="sources"></ol></footer>
</main>
<script>
const D = __DATA__;
const state = { format: D.formats[0], style: D.styles.includes(D.style) ? D.style : D.styles[0] };
try { const s = JSON.parse(localStorage.getItem("board") || "{}");
  if (D.formats.includes(s.format)) state.format = s.format;
  if (D.styles.includes(s.style)) state.style = s.style; } catch (e) {}
document.getElementById("title").textContent = D.title || "Storyboard";
document.getElementById("meta").textContent = D.scenes.length + " scenes, " + D.length + " s. Read the text under each frame aloud: it is the voice-over.";
function chips(id, list, key) {
  const box = document.getElementById(id);
  list.forEach(v => { const b = document.createElement("button"); b.textContent = v;
    b.onclick = () => { state[key] = v; try { localStorage.setItem("board", JSON.stringify(state)); } catch (e) {} draw(); };
    b.dataset.v = v; box.appendChild(b); });
}
chips("formats", D.formats, "format");
chips("styles", D.styles, "style");
if (D.warnings.length) {
  const w = document.getElementById("warn"); const box = document.createElement("div"); box.className = "warn";
  box.innerHTML = "<b>Check before the render</b>"; const ul = document.createElement("ul");
  D.warnings.forEach(x => { const li = document.createElement("li"); li.textContent = x; ul.appendChild(li); });
  box.appendChild(ul); w.appendChild(box);
}
D.sources.forEach(s => { const li = document.createElement("li"); li.textContent = s; document.getElementById("sources").appendChild(li); });
function draw() {
  document.querySelectorAll(".group button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === state[b.parentNode.id === "formats" ? "format" : "style"])));
  const tall = state.format === "vertical";
  const grid = document.getElementById("grid");
  grid.style.setProperty("--min", tall ? "200px" : state.format === "banner" ? "520px" : "320px");
  grid.innerHTML = "";
  const imgs = D.images[state.style + "/" + state.format] || [];
  D.scenes.forEach((s, i) => {
    const c = document.createElement("div"); c.className = "card";
    const im = document.createElement("img"); im.src = imgs[i] || ""; im.alt = s.id + " " + s.type; c.appendChild(im);
    const b = document.createElement("div"); b.className = "body";
    const h = document.createElement("div"); h.className = "head";
    h.innerHTML = "<b></b><span></span>"; h.children[0].textContent = s.id + " " + s.type;
    h.children[1].textContent = s.start.toFixed(1) + "-" + s.end.toFixed(1) + " s"; b.appendChild(h);
    if (s.caption) { const p = document.createElement("div"); p.className = "cap"; p.textContent = s.caption; b.appendChild(p); }
    const p = document.createElement("p"); p.className = "say"; p.textContent = s.text; b.appendChild(p);
    c.appendChild(b); grid.appendChild(c);
  });
}
draw();
</script>
"""
