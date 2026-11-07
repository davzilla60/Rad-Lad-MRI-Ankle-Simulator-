# MR-I Ready — MRI Ankle

An embeddable, single-file teaching simulator for the Rad-Lad website. It uses the same engine and layout as the
MR-I Ready shoulder simulator. Every diagnostic image comes from **one real, anonymised right-ankle MRI** and is shown
with its true scanner geometry. **It's a demonstration only.**

Marker: **The Achilles Advantage** — axial first, the sagittal and coronal angled to the long axis of the foot, key
anatomy covered, and the foot in the standard position.

## Flow

1. **Patient set-up.** The patient lies feet first with the right foot in a dedicated foot / ankle coil. Choose a
   position (the 3-D room changes pose):
   - supine, **foot at 90°**, toes straight up — the standard position;
   - supine, toes pointed about 20° — a peroneal tendon add-on, not the routine set-up;
   - prone, foot pointing down — an Achilles option in some departments, not the routine set-up.
2. **Localiser.** A 3-plane localiser is "acquired" line by line: each image is rebuilt from its own k-space with an
   inverse FFT as the phase-encode lines fill. The study had no localiser, so these are simulated (see `CREDITS.md`).
3. **Axial first.** The sagittal and coronal are locked until the axial has been scanned.
4. **Drag the axial in.** Completed series sit in a tray in the rail. Drag (or tap) the axial onto the **AXIAL** panel;
   only then does the rotate handle ⟳ appear on that panel. It opens at the sinus tarsi. Scroll (wheel or ▲ ▼) to a
   slice showing the heel and the talar head together.
5. **Angle on the axial.**
   - **Sagittal:** slices **parallel** to the long axis of the foot (Achilles insertion, talus, navicular).
   - **Coronal:** slices **perpendicular** to it.
   - The angle is graded against the radiographer's own sagittal plane in the DICOM (78.2° on the axial; the coronal
     reference is perpendicular to that, −11.8°), ±8°. SCAN stays locked until the angle is right.
   - The preview panel reformats the planned centre slice from the axial slices you actually acquired, so you can see
     the plane line up as you rotate.
6. **Scan → images.** Each scan shows only the real slices that fall inside your stack, cropped to your FOV.
7. **Debrief.** Coverage and angle for each plane, the position note, hero images (the axial shows your planes and the
   radiographer's dashed), a sequences-to-consider table, and the marker.

Boxes are projected onto each panel using its real IPP / IOP. Drag a box to move it, drag its edges to change coverage
or FOV, drag a ⟳ handle to angle it, or use the steppers / CLI (`slices`, `thick`, `gap`, `fov`, `angle`,
`use <series>`, `restore <plane>`, `help`).

## Files

- `ankle.embed.html` is the self-contained deliverable (~8.2 MB, every image inlined). `index.html` is an identical
  copy for one-drop hosting.
- `ankle.html` is the source. It loads `./assets/`, `assets/calib.js` and `room3d.js`. Run `python inline.py` to rebuild
  both deliverables.
- `room3d.js` is the procedural three.js MRI room (three.js from jsDelivr): magnet, three poses and the foot / ankle
  coil. The patient is feet first and not mirrored. If you change it, bump `?v=N` in `ankle.html` **and** `inline.py`
  together.
- `assets/` holds the simulated localisers (`loc_ax/cor/sag.png`), the series slices (`ax_pdfs`, `ax_t1`, `cor_pdfs`,
  `sag_pdfs`, `sag_t1`, `sag_gre`), `calib.json` / `calib.js` (true geometry of every image + landmarks) and the logos.
- `tools/gen_assets.py <study folder>` rebuilds `assets/` from the DICOM study (numpy + pillow only).
  `tools/landmarks.json` holds the hand-picked landmarks and localiser centres.

Debug hooks: `window.__mrk` (`parse(cmd)`, `gotoPlan(q)`, `useSeries(id)`, `setAngle(q, deg)`, `angErr(q)`, `autoPlan()`,
`analyse(q)`, `planOK(q)`, `finish()`, `S()`) and `window.__room()` (`setPose`, `cam`, `snap`).
