# pixel_science v0.1: design decisions

Agreed with Kosta in a grilling session on 2026-11-01. This file is the source for the v0.1 rebuild.

## Product

- Local tool + agent skills + asset library for short pixel-art science explainers. Open to the community.
- Users: anyone interested; first Kosta and other bioinformaticians.
- Agent first. The person types `/animate`. The skill runs the internal CLI `pixsci`; only people without an agent type `pixsci` by hand. Installed as a Claude Code / Codex plugin.
- Everything in the repo is in English (code, docs, on-screen text, voice). Discussion with Kosta is in Russian.
- License: MIT for code, CC0-1.0 for sprites (CC-BY-4.0 accepted for outside sprites, per file in CREDITS.csv).
- Length: 20 to 60 s. A longer video is several short ones.

## Formats

landscape 16:9 (1920x1080), vertical 9:16 (1080x1920), square 1:1 (1080x1080), banner 4:1 (1920x480). One plan renders all four; layout is relative to the frame.

## Workflow of /animate

1. Request (topic, viewer, formats).
2. Sources, then storyboard with the voice-over text for each scene. If the harness can publish artifacts, the storyboard is an HTML artifact (frames in each format, text to read, style switch); else PNG. The person accepts it.
3. The skill offers to record (or synthesize) the voice-over.
4. With a voice: `pixsci` makes a local transcript (faster-whisper `small.en`, installed on first use), finds where each scene starts by fuzzy match of the scene text, and times actions to words (`on: attacks`). Drift from the text is reported.
5. Without a voice: the animation is timed from the storyboard text (2.7 words/s).
6. Render in the chosen formats.

Storytelling and storyboard skills get their own design session later.

## Pace (enforced by `pixsci check`)

- A shot changes every 2 to 4 s.
- Something moves in every frame; a new action at least every 1.5 s.
- The final frame holds 3 s.
- Camera in action scenes: zoom, pan, shake, integer zoom only (x2, x3).

## Numbers

- Real numbers (from sources) are shown neatly, with no extra marks.
- Invented numbers (schematic N, rates) get no on-screen mark, but the skill warns the person before render.

## Styles: the cascade

A sprite is looked up by name; the most specific variant wins:

1. a PNG drawn for this style (`style-arcade/sprites/nk.png`);
2. a code sprite (`library.py`) drawn again with the style's parameters (outline, shading, number of tones);
3. the base indexed PNG, recolored with the style's palette (free default).

First styles: `paper` (light, PICO-8, current), `arcade` (dark, CRT scanlines, neon; Space Invaders, Galaga), `gameboy` (4 greens; Dr. Mario era). References: character-select screens, PICO-8 (lospec), Pedro Medeiros (saint11), Pixelblog (slynyrd). Take techniques and composition, never copy sprites.

## Everything is a pack

- A pack is a folder with `pack.yaml`. It can provide sprites, a style, scene types, backgrounds, a `bible.md` (roles and colors), examples. The core knows no pack.
- Packs stack; a higher pack overrides a lower one (the same cascade as styles).
- v0.1 packs: `biology` (cells, immunity, plants, fungi), `earth` (planet, meteorite, crater, dinosaurs, shock wave), `physics` (particles, fields, detector), and `style-paper`, `style-arcade`, `style-gameboy`.
- All packs live in this repo now. The format allows packs in other git repos later.
- A generated catalog (name, tags, animations, pack, license, thumbnail) lets the agent find sprites: `pixsci find immune --json`. The human cast sheet is built from the same catalog.

## Sprites

Drawn in code by the agent (`/add-sprite`) or contributed as PNG by artists. No AI-generated sprites.

## Procedural scenes

Generators inside action scenes, each with a `seed` (same seed, same video): `swarm` (N sprites, motion by rule), `grow` (division or growth by formula), `field` (flow of molecules, a field or gradient); color by rule (state, generation).

## Skills

- `/animate`: topic to video.
- `/add-sprite`: the agent draws a sprite in code, validates it, shows the sheet.

## Sound

Voice only in v0.1. Music and 8-bit sound effects later, as a pack.

## v0.1 scope and order

1. Core with packs and the style cascade; catalog; `--json` on all commands.
2. Styles paper, arcade, gameboy.
3. Voice: transcript, alignment to words.
4. Generators, camera, pace checks.
5. Storyboard artifact.
6. Videos: anti-PD-L1 mechanism, Higgs boson. The Missing-self demo is removed.

Next: mycorrhiza, the Chicxulub impact energy; then external packs, TTS, sound. The repo goes public after 3 to 5 videos and one outside sprite that passes the checks.

## Reusable assets and styles: 2026-11-05 decisions

Agreed with Kosta while discussing #26 (asset library) and #6 (styles). These decisions
update the style priorities above; they are a direction for the work, not a claim that
the style cascade or additional packs are implemented.

- **Reuse first.** Start with existing drawings, sprite frames, packs, and motion. Add
  a new drawing or abstraction only when an actual example needs it.
- **Shared palette (2026-11-07).** Kosta selected AAP-64 for future project art,
  shared across all subjects rather than fitted separately to each sprite. Existing
  PICO-8 code art keeps its indices; new PNG entries declare AAP-64 in the existing
  sprite metadata. Kosta selected a 128 px starting canvas for the receptor and
  requested simpler meaningful forms instead of dense surface detail. Smaller
  props need not fill that canvas; there is no mandatory square size for all assets.
- **Coverage.** First expand molecules, cells, laboratory equipment, organisms and
  plants, and water/weather. Laboratory mechanisms and everyday natural processes
  have equal priority. Geology, other physics, and astronomy follow later.
- **Detail.** Match the existing `tumor_pdl1`, `stem`, and `patient_a` sprites and the
  Cancer Wars character overview: distinct silhouettes, a few functional features,
  and readable states. Faces are optional. The same assets serve stills and video.
- **One base library.** Each sprite has one drawing and one set of animation frames
  in its domain pack, shared by all styles and light/dark environments. Its identity
  and meaningful colors remain recognizable. Adding a style must not require a new
  sprite collection. This supersedes the per-style sprite cascade above for this work.
- **Styles own environments.** Put the style's visual language in assembled environments,
  backgrounds, lighting, labels, and framing. Use the base sprite unchanged by default.
  If a demonstrated readability or harmony problem needs a slight palette adjustment,
  apply a small color mapping at draw time, preserving meaningful distinctions; keep
  the source PNG and animation frames shared. Do not produce per-style sprite files.
- **First comparison.** Use approved atlas directions 03 Moss & Vermilion Woodcut,
  09 Porcelain Solarpunk, and 17 Sepia Clockwork Draft on two identical subjects:
  a ligand binding a membrane receptor, and the water cycle.
- **Continuous explanation.** Keep the complete mechanism visible where useful,
  particularly for the water cycle. Guide attention with movement and highlighting;
  use readable silhouettes and compose each format independently. Add an enlarged
  detail only when the explanation needs it.
- **Color and motion.** Keep each object's colors consistent within a video. Use
  shape and labels as well as color. Begin with a static drawing; add sprite frames
  for meaningful changes such as filling, binding, or growth. Reuse ordinary motion.
- **Order.** Expand the shared base assets and check them on light and dark backgrounds.
  Develop styled environments separately, reusing those same assets. Style selection
  does not gate the base library. Validate complete examples in four formats before
  expanding widely. Production sprites and metadata belong in the existing pack
  structure; generated comparisons remain in `out/`.

First comparison prepared on 2026-11-05 in `out/style-showcase/preview.html`. After
Kosta clarified that the base library is shared, the study was corrected to use one
`base/assets/` folder and identical sprite pixels across all three environments.
The visual comparison remains a local study rather than an installed style pack.

Base-asset batch #42 ([PR #44](https://github.com/kostachernyshov/pixel_science/pull/44))
adds 30 biology sprites and 8 earth sprites in the production
pack structure. All original 70 sheets and metadata entries are unchanged. Validation
prints `108 sprites: VALID`; all 38 additions rebuild byte-for-byte. All 47 new
animation frames load through the existing sprite interface, and a mixed-pack smoke
plan passes `check` and renders storyboards in four formats. Light/dark review sheets
and state comparisons are in ignored `out/base-assets/`. The renderer's unrelated
text-only-summary crash is tracked separately in #43. Independent Standards and
Spec reviews found no actionable issues. Kosta approved the visual direction and
asked to continue; PR #44 remains open, not merged.

Two silent integration controls are in ignored `out/library-controls/`: a 27 s
water cycle and a 20 s ligand/receptor binding study. Both keep a fixed camera,
reuse pack sprites and existing mechanism profiles, and render in all four formats.
The eight exports were checked for dimensions, duration, frame count, and a stable
final hold. A light/dark comparison uses identical sprite sources without recoloring.
These are local visual checks, not narrated educational releases or installed
environment styles. Environment-style integration and the remaining #26 roadmap
stay open.

### Art direction correction — 2026-11-06

Kosta rejected the integration controls for their visual quality. Their technical
checks do not constitute artistic acceptance. The next step is one convincing
concept frame, followed by a short fidelity test against that frame, before more
formats or full videos. Use the existing RAG2/sarcoma animation as a reference for
continuous staging and action synchronized to narration, the approved style atlas
for composition/light/form, and 8bit Engineering for explanatory object interaction.
Reference observations and a first unapproved concept are in ignored
`out/art-direction/`. No renderer feature or sprite redesign is agreed by this study.

Following Kosta's requested sunny-to-rainy sequence, a nine-frame concept-art
storyboard is prepared in ignored `videos/water-cycle-woodcut/storyboard.md`
(44 s, 95-word narration draft). It keeps a thin stream before rain, delays the
runoff response, and finishes with the fuller stream entering the lake. The proposed
first implementation is only a short cloud-shadow/rain/stream-response fidelity
test using a cached master landscape and small changing regions. Kosta subsequently
accepted the storyboard with “действуй”. The first 8 s landscape fidelity test is
rendered under that video folder: fixed master art, cloud shadow, rain and delayed
stream widening. Render/encode measured 1.682 s for 240 frames at 1920×1080 on this
machine; the moving result still awaits artistic review. The core and production
sprite packs were not changed. The storyboard records the custom-scene model-check
limitation and separates the art-only check from causal validation.

Kosta accepted that moving test and requested the full story. On 2026-11-07 the
complete 44 s landscape version was rendered in labeled and clean forms, with a
reusable clean final PNG, in `videos/water-cycle-woodcut/out/story/`. It reuses the
same two art sources and implements cloud formation/travel, sunlight, schematic
vapor marks, rain, delayed stream filling, clearing and a 3 s final hold. Both
exports are 1920×1080, 30 fps, 1320 frames, without audio; the accepted narration
text is preserved separately. Measured render/encode times were approximately
7.65 s and 7.38 s. Alternate aspect ratios and spoken delivery remain separate
from this accepted-composition visual version. Core code and production packs
remain unchanged by the scene study.

### Ligand/receptor visual correction — 2026-11-07

Kosta rejected the original binding control's art and its depiction of a protein
ligand as a cell-like body carrying another binding head. A new concept in ignored
`videos/ligand-receptor/concept.md` depicts two folded molecular surfaces, with the
ligand's binding region integral to its own body and the receptor continuous through
the membrane. The CDK4/p16 sheet is an explicit reference for readable functional
regions, not a substitute for membrane-receptor biology. The requested sequence is
concept review, then sourced story/storyboard, then video. Only the first concept
has been prepared; its direction is not yet accepted. The old control is not a
scientifically or artistically approved reference.

Kosta liked the new molecular art and selected a ligand-triggered intracellular
response for the next storyboard. The scientific example is EGF/EGFR, but Kosta
explicitly requested a broadly reusable schematic receptor rather than an EGFR-only
drawing. The revised five-beat, 10-second story and asset contract are in ignored
`videos/ligand-receptor/storyboard.md`: two instances each of a shared protein
ligand and membrane receptor, intrinsic contact masks, a reusable bilayer, receptor
pairing, asymmetric kinase contact and a tail phosphate mark. Named biology belongs
to the scene; reuse must preserve the visible mechanism. The flattened concept is
not yet an exported sprite kit. Kosta liked the direction and asked to remove the
excess duration. The revised cut keeps binding, pairing, kinase activation, tail
phosphorylation and a two-second final hold. It reuses five endpoints from the
existing concept sheet without new generation. Source-asset preparation and the
first complete 10-second render remain to be done; no core or pack changes were made.

Kosta accepted the 10-second cut by asking for animation with pixel-science:animate.
The full silent version was rendered in four formats plus clean landscape under
`videos/ligand-receptor/out/`. Its first four-format render/encode measured 5.608 s,
excluding art preparation. At Kosta's subsequent request, the reusable library
exports were converted to the main 16 PICO-8 colors and binary transparency and
saved directly in the existing `packs/biology/sprites/` directory:
`protein_folded.png`, `membrane_receptor.png`, `membrane.png`. They use the existing
`sprites.json` and `CREDITS.csv`; the extra art folder, prompts and sidecars were
removed. The old `protein.png` is preserved. These compact library exports differ
in color/detail from the accepted movie; the movie files were not overwritten.
Kosta subsequently selected AAP-64 and 128 px receptor art with fewer meaningful
forms. The same three PNG entries now use explicit AAP-64 metadata; old code art
keeps its PICO-8 indices. Palette validation supports both declared palettes, and
the existing cast sheet fits larger sources. The shared receptor was redrawn with
broad lobes, a short neck and one inner region. No extra sprite folders or prompt
files were added. Prior movie exports remain preserved.
