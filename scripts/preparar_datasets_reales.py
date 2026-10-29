#!/usr/bin/env python3
"""Download real potato images; build separate classification/detection pilots.

No synthetic fallback, fabricated boxes, or overwriting existing datasets.
Only Pillow and PyYAML are required beyond the standard library.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
from pathlib import Path
import random
import shutil
import tempfile
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image
import yaml

BASE = Path(__file__).resolve().parents[1]
NAMES = {0: "tizon_tardio", 1: "tizon_temprano", 2: "hoja_sana"}
PV = {"Potato___Late_blight": 0, "Potato___Early_blight": 1, "Potato___healthy": 2}
PD = {"Potato leaf late blight": 0, "Potato leaf early blight": 1}
REPOS = {"plantvillage": "spMohanty/PlantVillage-Dataset",
         "plantdoc": "pratikkayal/PlantDoc-Object-Detection-Dataset"}
SPLITS = ("train", "val", "test")


def fetch(url):
    for attempt in range(4):
        try:
            request = Request(url, headers={"User-Agent": "IOTtesis-dataset-preparation"})
            with urlopen(request, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)


def image_info(path):
    with Image.open(path) as image:
        image.load()
        rgb = image.convert("RGB")
        digest = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
        return rgb.size, digest


def acquire(root, source):
    cache = root / "data" / "raw" / "fuentes_reales" / source
    cache.mkdir(parents=True, exist_ok=True)
    index_path = cache / "source_index.json"
    if index_path.exists():
        return cache, json.loads(index_path.read_text())
    repo = REPOS[source]
    revision = json.loads(fetch(f"https://api.github.com/repos/{repo}/commits/master"))["sha"]
    raw = f"https://raw.githubusercontent.com/{repo}/{revision}/"
    tree = json.loads(fetch(f"https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1"))
    records = []
    excluded = []
    if source == "plantvillage":
        # Fetch each class subtree explicitly: the repository-wide tree is truncated.
        for folder, cid in PV.items():
            prefix = "raw/color/" + folder
            entry = next(x for x in tree["tree"] if x["path"] == prefix)
            branch = json.loads(fetch(f"https://api.github.com/repos/{repo}/git/trees/{entry['sha']}?recursive=1"))
            if branch.get("truncated"):
                raise ValueError("Incomplete class listing: " + folder)
            for item in branch["tree"]:
                if item["type"] == "blob" and Path(item["path"]).suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    records.append({"source_path": prefix + "/" + item["path"], "class_id": cid,
                                    "source_group": item["path"].split("___")[0]})
    else:
        if tree.get("truncated"):
            raise ValueError("Incomplete PlantDoc listing")
        available = {x["path"] for x in tree["tree"]}
        for split, folder in [("train", "TRAIN"), ("test", "TEST")]:
            content = fetch(raw + split + "_labels.csv")
            (cache / (split + "_labels.csv")).write_bytes(content)
            grouped = defaultdict(list)
            for row in csv.DictReader(io.StringIO(content.decode("utf-8-sig"))):
                grouped[row["filename"]].append(row)
            for filename, rows in grouped.items():
                if not any(row["class"] in PD for row in rows):
                    if any(row["class"].startswith("Potato") for row in rows):
                        excluded.append({"path": folder + "/" + filename,
                                         "reason": "unconfirmed_healthy_or_other_class"})
                    continue
                # Exclude mixed-crop images: unlabelled non-potato leaves are not negatives.
                if any(row["class"] not in PD for row in rows):
                    excluded.append({"path": folder + "/" + filename, "reason": "mixed_crop_annotations"})
                    continue
                path = folder + "/" + filename
                if path not in available:
                    excluded.append({"path": path, "reason": "image_missing_from_upstream"})
                    continue
                records.append({"source_path": path, "annotations": rows,
                                "source_split": split, "source_group": filename})
    index = {"source": source, "repository": "https://github.com/" + repo,
             "revision": revision, "raw_base": raw, "records": records, "excluded": excluded}
    # Retain upstream attribution/licence text, without inventing a licence.
    legal = [x["path"] for x in tree["tree"] if "/" not in x["path"] and
             (x["path"].lower().startswith(("license", "readme", "citation")))]
    for name in legal:
        (cache / name).write_bytes(fetch(raw + quote(name, safe="/")))
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    return cache, index


def download_records(cache, index, workers):
    def download(record):
        record = dict(record)
        source_path = record["source_path"]
        suffix = Path(source_path).suffix.lower()
        key = hashlib.sha256(source_path.encode()).hexdigest()[:24]
        path = cache / "images" / (key + suffix)
        path.parent.mkdir(exist_ok=True)
        if not path.exists():
            content = fetch(index["raw_base"] + quote(source_path, safe="/"))
            tmp = path.with_suffix(".part")
            tmp.write_bytes(content)
            try:
                image_info(tmp)
                tmp.replace(path)
            finally:
                tmp.unlink(missing_ok=True)
        size, digest = image_info(path)
        record.update(cache_path=str(path), width=size[0], height=size[1], pixel_sha256=digest)
        return record
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, record in enumerate(pool.map(download, index["records"]), 1):
            results.append(record)
            if i % 100 == 0 or i == len(index["records"]):
                print(f"{index['source']}: {i}/{len(index['records'])} imágenes verificadas", flush=True)
    return results


def split_records(records, source):
    # Keep exact pixel duplicates and known filename groups in the same split.
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen = {}
    for i, record in enumerate(records):
        for key in [("pixels", record["pixel_sha256"]), ("group", record["source_group"])]:
            if key in seen:
                parent[find(i)] = find(seen[key])
            else:
                seen[key] = i
    groups = defaultdict(list)
    for i, record in enumerate(records):
        groups[find(i)].append(record)
    strata = defaultdict(list)
    for group in groups.values():
        classes = {r["class_id"] for r in group} if source == "plantvillage" else {
            PD[a["class"]] for r in group for a in r["annotations"]}
        if source == "plantvillage" and len(classes) > 1:
            raise ValueError("Conflicting labels on duplicate PlantVillage images")
        strata[tuple(sorted(classes))].append(group)
    rng = random.Random(42)
    for signature, items in sorted(strata.items()):
        rng.shuffle(items)
        n = len(items)
        nv = max(1, round(n * .15)) if n >= 3 else 0
        nt = max(1, round(n * .15)) if n >= 3 else 0
        for i, group in enumerate(items):
            split = "val" if i < nv else "test" if i < nv + nt else "train"
            for record in group:
                record["split"] = split
    return records


def yolo_boxes(record):
    boxes = []
    for row in record["annotations"]:
        w, h = record["width"], record["height"]
        if (int(row["width"]), int(row["height"])) != (w, h):
            raise ValueError("Annotation/image dimensions differ: " + record["source_path"])
        x1, y1, x2, y2 = [float(row[k]) for k in ("xmin", "ymin", "xmax", "ymax")]
        # Clip original edge coordinates to image bounds, reject empty boxes.
        x1, x2 = max(0, min(w, x1)), max(0, min(w, x2))
        y1, y2 = max(0, min(h, y1)), max(0, min(h, y2))
        if x2 <= x1 or y2 <= y1:
            raise ValueError("Empty bounding box: " + record["source_path"])
        boxes.append([PD[row["class"]], (x1+x2)/(2*w), (y1+y2)/(2*h), (x2-x1)/w, (y2-y1)/h])
    return boxes


def verify_dataset(destination):
    manifest = json.loads((destination / "manifest.json").read_text())
    if manifest.get("synthetic") is not False or manifest["task"] not in {"classify", "detect"}:
        raise ValueError("Expected an explicitly real classification/detection manifest")
    names = {int(k): v for k, v in manifest["classes"].items()}
    if manifest["task"] == "detect":
        config = yaml.safe_load((destination / "data.yaml").read_text())
        if config["nc"] != len(names) or config["names"] != names:
            raise ValueError("YAML taxonomy differs from the manifest")
    hashes, groups = {}, {}
    counts = {s: Counter() for s in SPLITS}
    instances = {s: Counter() for s in SPLITS}
    for record in manifest["records"]:
        path = destination / record["output_path"]
        size, digest = image_info(path)
        if digest != record["pixel_sha256"]:
            raise ValueError("Image checksum differs: " + str(path))
        split = record["split"]
        for key, mapping in [(digest, hashes), (record["source_group"], groups)]:
            if key in mapping and mapping[key] != split:
                raise ValueError("Data leakage across splits")
            mapping[key] = split
        if manifest["task"] == "detect":
            labels = destination / record["label_path"]
            lines = [line.split() for line in labels.read_text().splitlines() if line.strip()]
            expected = record["boxes"]
            if len(lines) != len(expected) or not lines:
                raise ValueError("Missing annotations: " + str(labels))
            for line, box in zip(lines, expected):
                if len(line) != 5 or int(line[0]) != box[0] or any(
                    abs(float(a)-b) > 1e-7 for a, b in zip(line[1:], box[1:])):
                    raise ValueError("Invalid labels: " + str(labels))
                cid, x, y, bw, bh = map(float, line)
                if not (int(cid) in names and 0 < bw <= 1 and 0 < bh <= 1 and
                        x-bw/2 >= -1e-7 and y-bh/2 >= -1e-7 and
                        x+bw/2 <= 1+1e-7 and y+bh/2 <= 1+1e-7):
                    raise ValueError("Box outside image")
                instances[split][names[int(cid)]] += 1
            for cid in {box[0] for box in expected}:
                counts[split][names[cid]] += 1
        else:
            counts[split][names[record["class_id"]]] += 1
    if any(counts[s][name] == 0 for s in SPLITS for name in names.values()):
        raise ValueError("At least one class is absent from a split")
    report = {"source": manifest["source"], "task": manifest["task"],
              "images": len(manifest["records"]), "images_per_class": counts,
              "boxes_per_class": instances, "exact_duplicate_leakage": False,
              "notes": manifest["limitations"]}
    (destination / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def prepare(root, source, workers):
    destination = root / "data" / "processed" / (
        "papa_plantvillage_clasificacion" if source == "plantvillage" else "papa_plantdoc_yolo")
    if destination.exists():
        print(json.dumps(verify_dataset(destination), indent=2, ensure_ascii=False), flush=True)
        return
    cache, index = acquire(root, source)
    # A generic 'Potato leaf' label does not establish a healthy diagnosis.
    # Filter old cached indexes too, without altering their provenance.
    index = dict(index)
    excluded = list(index.get("excluded", []))
    if source == "plantdoc":
        eligible = []
        for record in index["records"]:
            if any(row["class"] not in PD for row in record["annotations"]):
                excluded.append({"path": record["source_path"], "reason": "unconfirmed_healthy_or_other_class"})
            else:
                eligible.append(record)
        index["records"] = eligible
    records = split_records(download_records(cache, index, workers), source)
    task = "classify" if source == "plantvillage" else "detect"
    limitations = ["Pilot with public images; not a validation in the La Paz greenhouse.",
                   "Split by source filename groups and exact decoded pixel hashes; near-duplicates and physical plant identity need manual review.",
                   "70/15/15 approximately by groups, not necessarily by image count; seed=42."]
    if task == "detect":
        limitations += ["Boxes delimit whole leaves, not lesions. Do not calculate lesion severity from these boxes.",
                        "Original TRAIN/TEST recombined for a two-disease pilot. This is not the official PlantDoc benchmark.",
                        "Generic Potato leaf images excluded: source label does not confirm healthy status. Disease labels also require agronomic review."]
    names = NAMES if task == "classify" else {k: NAMES[k] for k in PD.values()}
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".papa-preparacion-", dir=destination.parent))
    try:
        for record in records:
            split = record["split"]
            name = Path(record["cache_path"]).name
            if task == "classify":
                output = Path(split) / NAMES[record["class_id"]] / name
            else:
                output = Path("images") / split / name
                record["boxes"] = yolo_boxes(record)
                label = Path("labels") / split / (Path(name).stem + ".txt")
                (stage / label).parent.mkdir(parents=True, exist_ok=True)
                (stage / label).write_text("".join("%d %.9f %.9f %.9f %.9f\n" % tuple(b) for b in record["boxes"]))
                record["label_path"] = str(label)
            (stage / output).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(record["cache_path"], stage / output)
            record["output_path"] = str(output)
            record["source_url"] = index["raw_base"] + quote(record["source_path"], safe="/")
            del record["cache_path"]
        manifest = {"source": source, "repository": index["repository"], "revision": index["revision"],
                    "task": task, "classes": names, "seed": 42, "synthetic": False,
                    "limitations": limitations, "records": records, "excluded": excluded}
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        if task == "detect":
            config = {"path": str(destination.resolve()), "train": "images/train", "val": "images/val",
                      "test": "images/test", "nc": len(names), "names": names}
            (stage / "data.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
        report = verify_dataset(stage)
        stage.rename(destination)
    except Exception:
        shutil.rmtree(stage)
        raise
    print("Dataset real preparado: " + str(destination), flush=True)
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["plantvillage", "plantdoc", "all"], default="all")
    parser.add_argument("--root", type=Path, default=BASE)
    parser.add_argument("--workers", type=int, choices=range(1, 17), default=8)
    parser.add_argument("--verify", action="store_true", help="Validate existing datasets without network")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    for source in REPOS if args.source == "all" else [args.source]:
        if args.verify:
            folder = "papa_plantvillage_clasificacion" if source == "plantvillage" else "papa_plantdoc_yolo"
            print(json.dumps(verify_dataset(root / "data" / "processed" / folder), indent=2, ensure_ascii=False))
        else:
            prepare(root, source, args.workers)


if __name__ == "__main__":
    main()
