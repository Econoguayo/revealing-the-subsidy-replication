"""Check the package against MANIFEST.sha256 and the model component against its frozen manifest.

Usage: python tools/verify_manifest.py [PACKAGE_ROOT]            verify
       python tools/verify_manifest.py PACKAGE_ROOT --write      rewrite MANIFEST.sha256 (maintainer only)

1. Every file listed in MANIFEST.sha256 must exist with the listed SHA-256; files present but not
   listed are reported. The folders _rerun/ and .git/ are ignored.
2. Every file in 3_model/ must match the 16-character SHA-256 prefix recorded for it in
   3_model/manifest_all.json, the manifest of the frozen archive lpvs_tractability_2026-11-04a.zip
   (full archive SHA-256 f978159c69434146fd94a986ec6f8cba90cba1ce643a809fbb98226f2954012d). Archive files
   not included in this package are listed.
The last line of the output is a one-line verdict.
"""
import hashlib, json, os, sys

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {"_rerun", ".git", "__pycache__", ".pytest_cache"}
SKIP_FILES = {"MANIFEST.sha256"}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def files():
    for dp, dns, fs in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
        for f in sorted(fs):
            rel = os.path.relpath(os.path.join(dp, f), root).replace("\\", "/")
            if rel not in SKIP_FILES:
                yield rel


if "--write" in sys.argv:
    with open(os.path.join(root, "MANIFEST.sha256"), "w", encoding="utf-8", newline="\n") as fh:
        for rel in files():
            fh.write(f"{sha(os.path.join(root, rel))}  {rel}\n")
    print("MANIFEST.sha256 written")
    sys.exit(0)

listed = {}
for line in open(os.path.join(root, "MANIFEST.sha256"), encoding="utf-8"):
    if line.strip():
        h, rel = line.rstrip("\n").split("  ", 1)
        listed[rel] = h
bad, missing = [], []
for rel, h in listed.items():
    path = os.path.join(root, rel)
    if not os.path.exists(path):
        missing.append(rel)
    elif sha(path) != h:
        bad.append(rel)
extra = [rel for rel in files() if rel not in listed]
for rel in missing:
    print("missing:", rel)
for rel in bad:
    print("hash differs:", rel)
for rel in extra:
    print("not in manifest:", rel)

frozen = json.load(open(os.path.join(root, "3_model", "manifest_all.json"), encoding="utf-8"))["files"]
model_bad, model_extra = [], []
for dp, _, fs in os.walk(os.path.join(root, "3_model")):
    if any(s in dp for s in SKIP_DIRS):
        continue
    for f in fs:
        rel = os.path.relpath(os.path.join(dp, f), os.path.join(root, "3_model")).replace("\\", "/")
        if rel == "manifest_all.json":
            continue
        if rel not in frozen:
            model_extra.append(rel)
        elif sha(os.path.join(dp, f))[:16] != frozen[rel]:
            model_bad.append(rel)
present = {os.path.relpath(os.path.join(dp, f), os.path.join(root, "3_model")).replace("\\", "/")
           for dp, _, fs in os.walk(os.path.join(root, "3_model")) for f in fs}
omitted = sorted(set(frozen) - present)
for rel in model_bad:
    print("3_model file differs from the frozen archive:", rel)
for rel in model_extra:
    print("3_model file not in the frozen archive:", rel)
print(f"frozen archive files not included in 3_model/ ({len(omitted)}): {', '.join(omitted)}")
n = len(listed)
if missing or bad or model_bad or model_extra:
    print(f"DIFFERS: integrity check failed ({len(missing)} missing, {len(bad)} changed, {len(model_bad) + len(model_extra)} model files off the frozen manifest)")
else:
    print(f"integrity check passed: {n} files match MANIFEST.sha256 ({len(extra)} unlisted); "
          f"{len(present) - 1} model files match the frozen manifest of version 2026-11-04a")
