# Credits

## MRI imaging — "MRI / Ankle / Patient 1"

**Adapted from:** one anonymised MRI study of an ankle from the Prometheus library (GE SIGNA Pioneer 3 T, 8-channel
foot / ankle coil, feet first supine). The headers hold no sequence descriptions or side, so the names below are
inferred from TR / TE, and a right ankle is inferred from the anatomy and table position. Series used:

- axial PD FS (TR 2412 / TE 35) and axial T1 (TR 435 / TE 11)
- coronal PD FS (TR 5248 / TE 39)
- sagittal PD FS (TR 4533 / TE 46), sagittal T1 (TR 747 / TE 11) and sagittal GRE (TR 607 / TE 13)

### Changes made

1. **Digitally edited images.** An area of calcaneal marrow is synthesised in 50 of the 220 slices. These images are
   teaching data, not a diagnostic record, and the trabeculae in that area don't line up between slices or planes the
   way real ones do.
2. Pixel values were windowed (99.7th percentile per series) to 8-bit and saved as JPEG. The 1024 px T1 series were
   averaged down to 512 px.
3. The DICOM geometry (ImagePositionPatient, ImageOrientationPatient, PixelSpacing) is kept in `assets/calib.json` and
   drives all the planning overlays. Only the T1 pixel spacing and first-pixel position change, to match the 512 px
   images.
4. **Localisers are simulated.** The study had none. Scanner-true 8 mm slabs were resampled from the real axial and
   sagittal T1 stacks on a 200 mm / 256 grid. Contrast was flattened, then coil shading, k-space truncation (256 × 160)
   and Rician noise were added. The localiser animation is a real inverse FFT of those images.
5. Fifteen anatomical landmarks were picked by hand on the real slices and are approximate (±5 mm).
6. The radiographer's sagittal angle (78.2° in the axial plane) is the grading reference, and the coronal reference is
   perpendicular to it (the real coronal is −8.0°).
7. In the browser: the planning previews are reformats of the acquired axial slices; scans show only the real slices
   inside the planned stack, cropped to the planned FOV. Foot position doesn't change the images.
8. The clinical scenario is fictional. The 3-D room shows a generic closed-bore magnet.
9. Sequences other than those listed above are for teaching only. There are no images for them.

Educational simulation. It isn't a medical device and isn't for clinical use.
