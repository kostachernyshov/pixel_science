# Physics pack: roles and colors

Check every frame in greyscale: the roles must still read.

## Particles

Matter particles are characters: a white body, a colored rim fixed for each particle, dot eyes.
Size follows mass in spirit, not in scale: heavier particles are drawn larger.

| Particle | Sprite | Rim | Note |
|---|---|---|---|
| Electron | `electron` | blue | small |
| Proton | `proton` | orange | three quark dots inside: two up (pink), one down (green) |
| Top quark | `top_quark` | plum | large: the heaviest known elementary particle |
| Higgs boson | `higgs` | yellow body, orange rim | the only particle with a colored body |

Light is not a character: `photon` is a yellow wave packet with no face.

## Fields

A field is drawn as a quiet lattice of small dots (the `field` generator, `kind: dots`), lavender or light grey.
A particle that interacts with the field gathers dots around it (`drag`); one that does not, passes through.

## Machines

`detector` is a generic cross-section (beam pipe, tracker, calorimeter, muon layer). Never draw the logo or
the exact shape of a real experiment.

## Rules

- Analogies are named as analogies in the voice-over; the picture never claims more than the voice.
- Numbers on screen come from a source and are listed under `numbers:` in the plan.
