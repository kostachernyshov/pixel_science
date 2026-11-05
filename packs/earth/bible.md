# Water, weather, and soil base assets

`sun`, `cloud`, `water_drop`, `snowflake`, `ice`, `water_pool`, `river`, and `soil`
are shared base sprites. Environments supply the terrain, sky, atmosphere, and
composition. Reuse the same sprite files across styles and frame formats.

- `cloud` means a cloud, not water vapour. Use actor paths/arrows for invisible
  vapour transport, not a visible gas-puff sprite.
- `soil/wet` shows blue pore marks in the lower layer. It does not depict an
  underground lake or imply that groundwater normally fills open caverns.
- `river` is an isolated bend of water, without baked banks or a landscape.
- `snowflake` has six primary arms. All shapes, scales, and colors are schematic.
- All assets have one `idle` frame; `soil` also has a static `wet` state. Use existing
  actor movement to animate rain, snow, or a process route.

[USGS: Water Cycle](https://www.usgs.gov/water-science-school/water-cycle) and
[USGS: Water Cycle Terms](https://www.usgs.gov/glossary/glossary-water-cycle-terms)
inform the concepts. The drawings are original code; no source illustrations are copied.

Code: MIT. PNG sprites: CC0-1.0. Credits: `sprites/CREDITS.csv`.
