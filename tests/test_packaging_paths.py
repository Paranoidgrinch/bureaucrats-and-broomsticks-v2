from pathlib import Path

from bab.content import data_loader


def test_application_root_uses_pyinstaller_bundle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(data_loader.sys, "frozen", True, raising=False)
    monkeypatch.setattr(data_loader.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert data_loader._application_root() == tmp_path


def test_source_project_root_contains_default_act_manifest() -> None:
    manifest = data_loader.PROJECT_ROOT / "data" / "acts" / "act_1_city.json"

    assert manifest.is_file()
