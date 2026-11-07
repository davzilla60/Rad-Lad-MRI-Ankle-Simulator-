"""Build ../assets from the ankle MRI study (Prometheus "MRI/Ankle/Patient 1").

    python -I tools/gen_assets.py "D:/Prometheus/MRI/Ankle/Patient 1/A20261107100853 - calcaneal mass removed"

Needs numpy + pillow only (a small reader below handles this study's implicit-VR little-endian files).
Writes loc_ax/cor/sag.png (simulated tri-plane localisers), <series>_NN.jpg slices, and calib.json / calib.js holding
the true DICOM geometry (IPP / IOP / pixel spacing) of every image plus the hand-picked anatomical landmarks.
All coordinates are DICOM patient (LPS) millimetres. Only pixels and geometry are read from the study: no descriptive
header text reaches the simulator, and every sequence label comes from SERIES below.
"""
import json, os, shutil, struct, sys
import numpy as np
from PIL import Image

ROOT = sys.argv[1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "assets")
os.makedirs(OUT, exist_ok=True)


# ---- minimal DICOM reader (implicit VR little endian, no sequences used) ----
def read(path):
    b = open(path, "rb").read()
    i, h = 132, {}
    while struct.unpack_from("<H", b, i)[0] == 2:              # file meta is explicit
        vr = b[i + 4:i + 6]
        if vr in (b"OB", b"UN", b"OW"):
            ln, p = struct.unpack_from("<I", b, i + 8)[0], i + 12
        else:
            ln, p = struct.unpack_from("<H", b, i + 6)[0], i + 8
        i = p + ln
    while i + 8 <= len(b):
        g, e, ln = struct.unpack_from("<HHI", b, i)
        p = i + 8
        if (g, e) == (0x7FE0, 0x0010):
            h["px"] = np.frombuffer(b, "<i2", ln // 2, p)
            break
        if ln != 0xFFFFFFFF:
            h[(g, e)] = b[p:p + ln]
            i = p + ln
        else:
            i = p
    t = lambda k: h[k].decode("latin-1").strip(" \0")
    f = lambda k: [float(x) for x in t(k).split("\\")]
    rows, cols = [struct.unpack("<H", h[(0x28, k)])[0] for k in (0x10, 0x11)]
    return {"series": int(t((0x20, 0x11))), "inst": int(t((0x20, 0x13))), "ipp": f((0x20, 0x32)), "iop": f((0x20, 0x37)),
            "ps": f((0x28, 0x30))[0], "thk": f((0x18, 0x50))[0], "rows": rows, "cols": cols,
            "a": h["px"].reshape(rows, cols).astype(np.float32)}


folder = os.path.join(ROOT, "P00001", "S0001")
ALL = [read(os.path.join(folder, f)) for f in sorted(os.listdir(folder)) if f.lower().endswith(".dcm")]

# (DICOM series, id, plane, label, params, est. seconds per acquisition, max slices per TR, shipped size)
# Labels are inferred from TR / TE: the source headers have no sequence descriptions.
SERIES = [
    (4, "ax_pdfs",  "ax",  "PD FS", "TR 2412 · TE 35", 200, 16, 512),
    (5, "ax_t1",    "ax",  "T1",    "TR 435 · TE 11",  170, 20, 512),
    (6, "cor_pdfs", "cor", "PD FS", "TR 5248 · TE 39", 210, 40, 512),
    (7, "sag_pdfs", "sag", "PD FS", "TR 4533 · TE 46", 190, 36, 512),
    (8, "sag_t1",   "sag", "T1",    "TR 747 · TE 11",  160, 30, 512),
    (9, "sag_gre",  "sag", "GRE",   "TR 607 · TE 13",  190, 34, 512),
]
SCALE_HI = 99.7


def shrink(a, n):
    if a.shape[0] == n:
        return a
    f = a.shape[0] // n
    return a.reshape(n, f, n, f).mean(axis=(1, 3))


calib = {"loc": {"n": 256}, "ser": {}}
VOL = {}
for num, sid, plane, label, params, secs, maxsl, size in SERIES:
    ds = sorted((d for d in ALL if d["series"] == num), key=lambda d: d["inst"])
    stack = np.stack([shrink(d["a"], size) for d in ds])
    hi = np.percentile(stack[stack > stack.max() * 0.02], SCALE_HI)
    v8 = np.clip(stack / hi, 0, 1) * 255
    for k in range(len(ds)):
        Image.fromarray(v8[k].round().astype(np.uint8)).save(os.path.join(OUT, "%s_%02d.jpg" % (sid, k)), quality=84, optimize=True)
    row = np.array(ds[0]["iop"][:3]); col = np.array(ds[0]["iop"][3:])
    f = ds[0]["rows"] / size
    ps = ds[0]["ps"] * f
    ipps = [np.array(d["ipp"]) + (row + col) * ds[0]["ps"] * (f - 1) / 2 for d in ds]   # centre of the new first pixel
    step = ipps[1] - ipps[0]
    sp = float(np.linalg.norm(step))
    nrm = step / sp
    calib["ser"][sid] = {"ipp": [[round(float(x), 3) for x in p] for p in ipps], "row": [round(float(x), 5) for x in row],
                         "col": [round(float(x), 5) for x in col], "ps": round(float(ps), 6), "cols": size, "rows": size,
                         "plane": plane, "seq": label, "params": params, "n": len(ds), "nrm": [round(float(x), 5) for x in nrm],
                         "sp": round(sp, 3), "thk": ds[0]["thk"], "secs": secs, "maxsl": maxsl}
    VOL[sid] = (v8, np.array(ipps[0]), row, col, nrm, ps, sp)


# ---- simulated localiser: scanner-true slabs resampled from the real T1 stacks ----
def sample(sid, P):
    """Trilinear sample of a stack at points P (..., 3). Returns value and an inside-the-stack mask."""
    v, o, row, col, nrm, ps, sp = VOL[sid]
    d = P - o
    i, j, k = d @ row / ps, d @ col / ps, d @ nrm / sp
    n, h, w = v.shape
    ok = (i >= 0) & (j >= 0) & (k >= 0) & (i < w - 1) & (j < h - 1) & (k < n - 1)
    i0, j0, k0 = [np.clip(np.floor(x).astype(int), 0, m - 2) for x, m in ((i, w), (j, h), (k, n))]
    fi, fj, fk = np.clip(i - i0, 0, 1), np.clip(j - j0, 0, 1), np.clip(k - k0, 0, 1)
    out = 0
    for dk in (0, 1):
        for dj in (0, 1):
            for di in (0, 1):
                wt = (fk if dk else 1 - fk) * (fj if dj else 1 - fj) * (fi if di else 1 - fi)
                out = out + wt * v[k0 + dk, j0 + dj, i0 + di]
    return np.where(ok, out, 0), ok


LOC_N, LOC_FOV = 256, 200.0
LOC_PS = LOC_FOV / LOC_N
CENTRE = json.load(open(os.path.join(HERE, "tools", "landmarks.json")))["loc_centre"]
LOC = {"ax": ((1, 0, 0), (0, 1, 0), (0, 0, 1)), "cor": ((1, 0, 0), (0, 0, -1), (0, 1, 0)), "sag": ((0, 1, 0), (0, 0, -1), (1, 0, 0))}
rng = np.random.default_rng(7)
SLAB = 8.0
for p, (r, c, n) in LOC.items():
    r, c, n = np.array(r, float), np.array(c, float), np.array(n, float)
    C = np.array(CENTRE[p], float)
    ipp = C - r * LOC_PS * (LOC_N - 1) / 2 - c * LOC_PS * (LOC_N - 1) / 2
    jj, ii = np.mgrid[0:LOC_N, 0:LOC_N]
    P0 = ipp + ii[..., None] * LOC_PS * r + jj[..., None] * LOC_PS * c
    acc, wt = np.zeros((LOC_N, LOC_N)), np.zeros((LOC_N, LOC_N))
    for t in np.linspace(-SLAB / 2, SLAB / 2, 7):
        P = P0 + n * t
        for sid in ("ax_t1", "sag_t1"):
            v, ok = sample(sid, P)
            acc += v * ok
            wt += ok
    a = np.where(wt > 0, acc / np.maximum(wt, 1), 0)
    # low-resolution GRE look: flatten contrast, coil shading, k-space truncation (256 x 160), Rician noise
    a = (a / 255.0) ** 0.8
    yy, xx = (jj - 128) / 128.0, (ii - 128) / 128.0
    a = a * (1.0 - 0.28 * (xx ** 2 + yy ** 2))
    K = np.fft.fftshift(np.fft.fft2(a))
    K[:, :48] = 0; K[:, -48:] = 0                               # keep 160 of 256 lines
    a = np.abs(np.fft.ifft2(np.fft.ifftshift(K)))
    a = np.hypot(a + rng.normal(0, 0.012, a.shape), rng.normal(0, 0.012, a.shape))
    a = np.clip(a / np.percentile(a, 99.7), 0, 1) * 255
    Image.fromarray(a.round().astype(np.uint8)).save(os.path.join(OUT, "loc_%s.png" % p), optimize=True)
    calib["loc"][p] = {"ipp": [round(float(x), 3) for x in ipp], "row": list(map(float, r)), "col": list(map(float, c)),
                       "ps": LOC_PS, "cols": LOC_N, "rows": LOC_N}

# ---- anatomical landmarks + the radiographer's own angles ----
extra = json.load(open(os.path.join(HERE, "tools", "landmarks.json")))


def P(sid, k, i, j):
    """Series id, 0-based slice, column and row on the shipped image -> LPS mm."""
    s = calib["ser"][sid]
    return [round(float(x), 1) for x in np.add(s["ipp"][k], np.add(np.multiply(s["row"], i * s["ps"]), np.multiply(s["col"], j * s["ps"])))]


calib["lm"] = {k: P(*v) for k, v in extra["lm"].items()}
ang = lambda r: round(float(np.degrees(np.arctan2(r[1], r[0]))), 1)
calib["real"] = {"cor": ang(calib["ser"]["cor_pdfs"]["row"]), "sag": ang(calib["ser"]["sag_pdfs"]["row"])}

json.dump(calib, open(os.path.join(OUT, "calib.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(os.path.join(OUT, "calib.js"), "w", encoding="utf-8").write("window.MRK_CALIB=" + json.dumps(calib, separators=(",", ":"), ensure_ascii=False) + ";\n")
print("ok", {k: v["n"] for k, v in calib["ser"].items()}, calib["real"], calib["lm"])
