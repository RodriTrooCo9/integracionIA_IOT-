"""Offline regression checks; fixture images are only test data, never training data."""
import importlib.util
import json
from pathlib import Path

from PIL import Image
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/preparar_datasets_reales.py"
spec = importlib.util.spec_from_file_location("datasets_reales", MODULE_PATH)
datasets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(datasets)


def test_duplicates_and_source_groups_cannot_cross_splits():
    records = [{"class_id": cid, "pixel_sha256": f"{cid}-{i}",
                "source_group": f"{cid}-{i}"} for cid in range(3) for i in range(20)]
    records += [dict(records[0]), dict(records[1], pixel_sha256="different-capture")]
    result = datasets.split_records(records, "plantvillage")
    for field in ["pixel_sha256", "source_group"]:
        seen = {}
        for record in result:
            assert seen.setdefault(record[field], record["split"]) == record["split"]
    for cid in range(3):
        assert {r["split"] for r in result if r["class_id"] == cid} == {"train", "val", "test"}
    assert [r["split"] for r in datasets.split_records(records, "plantvillage")] == [r["split"] for r in result]


def test_conflicting_duplicate_labels_are_rejected():
    records = [{"class_id": cid, "pixel_sha256": "same-pixels", "source_group": str(cid)}
               for cid in [0, 1]]
    with pytest.raises(ValueError, match="Conflicting"):
        datasets.split_records(records, "plantvillage")


def annotation(**overrides):
    row = {"width": "100", "height": "80", "class": "Potato leaf late blight",
           "xmin": "10", "ymin": "20", "xmax": "90", "ymax": "60"}
    row.update(overrides)
    return {"width": 100, "height": 80, "source_path": "leaf.jpg", "annotations": [row]}


def test_real_box_conversion_and_invalid_dimensions():
    assert datasets.yolo_boxes(annotation()) == [[0, .5, .5, .8, .5]]
    with pytest.raises(ValueError, match="dimensions"):
        datasets.yolo_boxes(annotation(width="200"))
    with pytest.raises(ValueError, match="Empty"):
        datasets.yolo_boxes(annotation(xmax="10"))


def test_verification_detects_image_tampering_and_missing_classes(tmp_path):
    path = tmp_path / "image.jpg"
    Image.new("RGB", (10, 10), "green").save(path)
    _, digest = datasets.image_info(path)
    manifest = {"source": "test-fixture", "task": "classify", "synthetic": False,
                "limitations": [], "classes": datasets.NAMES,
                "records": [{"output_path": "image.jpg", "pixel_sha256": digest,
                             "source_group": "plant1", "split": "train", "class_id": 0}]}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="absent"):
        datasets.verify_dataset(tmp_path)
    Image.new("RGB", (10, 10), "red").save(path)
    with pytest.raises(ValueError, match="checksum"):
        datasets.verify_dataset(tmp_path)


def test_synthetic_manifest_cannot_pass_as_real(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"synthetic": True, "task": "classify"}))
    with pytest.raises(ValueError, match="explicitly real"):
        datasets.verify_dataset(tmp_path)
