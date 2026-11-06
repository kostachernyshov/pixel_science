# Biology base assets

One source drawing and animation set per sprite, shared by light/dark environments
and every visual style. Use ordinary actor movement for static sprites. A new style
does not require new biology PNGs.

## Selection

| Need | Base sprites | Reuse guidance |
|---|---|---|
| Molecules | `protein`, `protein_folded`, `membrane_receptor`, `membrane`, `rna`, `lipid`, `plasmid`, `dna_fragment`, `peptide_self`, `peptide_mutant`, `proteasome`, `vesicle` | Protein and receptor shapes are reusable symbols, not solved structures. Functional sites are intrinsic regions of each molecule. |
| Cell machinery | `nucleus`, `mitochondrion`, `chloroplast`, `ribosome` | Internal features identify the organelle; pixel counts do not encode quantities. |
| Microorganisms | `bacterium`, `virus` | A generic rod-shaped bacterium and an enveloped viral particle; not all bacteria/viruses have these shapes. |
| Laboratory | `pipette`, `microscope`, `centrifuge`, `pcr_machine`, `gel` | Existing `tube`, `plate`, `dish`, `syringe`, `sequencer`, and vials remain shared. The centrifuge is drawn open to expose its rotor. |
| Organs | `heart`, `lungs`, `liver`, `brain` | Existing `kidney` completes this first organ set. These are identifiers, not diagnostic or anatomical diagrams. |
| Model organisms | `zebrafish`, `fruit_fly`, `nematode` | Existing `mouse_side` and `mouse_top` cover mice. |
| Plants | `seed`, `leaf`, `flower` | `seed/germinate` ends in a seedling. Tree/root drawings are already proposed in PR #19; do not redraw them in parallel. |

Reuse existing `epithelial` and `stem` for ordinary body cells, `dna` for the complete
helix, `badge_mhc*` for MHC symbols, and `antibody` for an antibody. A badge can also be
placed as a standalone actor. New gene/protein names normally need labels and model
parts, not a new sprite drawing.

## Meaningful states

- `seed/germinate`: four frames, seed to seedling, then holds. No species or growth
  timescale is implied.
- `gel/run`: four schematic band positions, then holds. Band positions/colors are
  illustrative, not experimental data or molecular-size measurements.
- `peptide_mutant`: one orange central bead and a shape mark distinguish it from
  `peptide_self`. Neither represents a specific peptide sequence.

Everything else added in this set starts with a single `idle` frame. Existing cells
keep their original animation sets. The original code-drawn additions use the PICO-8 base palette,
binary transparency, the existing outline/build pass, and pack metadata/credits.
New PNG art follows AAP-64 and size guidance in `CONTRIBUTING.md`. The shared
`membrane_receptor`, `protein_folded` and `membrane` use explicit AAP-64 entries;
the receptor is a simplified single-pass symbol, not an EGFR structural portrait.

## Scientific references

These inform what features to distinguish; no reference art is copied.

- [NHGRI: RNA](https://www.genome.gov/genetics-glossary/Ribonucleic-Acid-RNA): distinguish
  a single strand from the existing DNA helix.
- [NHGRI: Plasmid](https://www.genome.gov/genetics-glossary/Plasmid): circular DNA.
- [MedlinePlus: What is a cell?](https://medlineplus.gov/genetics/understanding/basics/cell/):
  nucleus, mitochondria, and ribosomes as distinct cell structures.
- [RCSB PDB-101: Proteasome](https://pdb101.rcsb.org/motm/166): a barrel-shaped protein
  degradation assembly, simplified here to a small icon.

Art code is MIT; PNG sprites are CC0-1.0, with authorship in `sprites/CREDITS.csv`.
