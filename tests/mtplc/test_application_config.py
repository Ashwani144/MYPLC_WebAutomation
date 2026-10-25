from __future__ import annotations

import pytest

from mtplc.config import application_config


def _write_workbook_with_model_numbers(
    workbook_path,
    model_numbers: tuple[str, ...],
) -> None:
    from zipfile import ZipFile

    namespace = (
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    )
    rows = [
        (
            "<row r='1'><c r='A1' t='inlineStr'><is><t>Model Number"
            "</t></is></c></row>"
        )
    ]
    rows.extend(
        (
            f"<row r='{index + 2}'><c r='A{index + 2}' t='inlineStr'>"
            f"<is><t>{model_number}</t></is></c></row>"
        )
        for index, model_number in enumerate(model_numbers)
    )
    worksheet = (
        f"<worksheet xmlns='{namespace}'><sheetData>{''.join(rows)}"
        "</sheetData></worksheet>"
    )
    with ZipFile(workbook_path, "w") as workbook:
        workbook.writestr("xl/worksheets/sheet1.xml", worksheet)


def test_explicit_application_uses_matching_workbook_without_template(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workbook = tmp_path / "Supplier-P-254470.xlsx"
    workbook.touch()
    (tmp_path / "Unrelated-P-254466_Template.xlsx").touch()

    monkeypatch.setattr(
        application_config,
        "_model_numbers",
        lambda workbook_path: ("MODEL-470", "MODEL-471"),
    )

    result = application_config.discover_application_config(
        downloads_dir=tmp_path,
        application_number="P-254470",
    )

    assert result.application_number == "P-254470"
    assert result.application_id == "254470"
    assert result.model_template_path == workbook
    assert result.expected_model_number == "MODEL-470"
    assert result.expected_model_numbers == ("MODEL-470", "MODEL-471")


def test_target_application_can_use_explicit_different_model_workbook(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workbook = tmp_path / "Supplier-P-254471.xlsx"
    workbook.touch()
    (tmp_path / "Supplier-P-254482_Template.xlsx").touch()

    monkeypatch.setattr(
        application_config,
        "_model_numbers",
        lambda workbook_path: ("MODEL-482",),
    )

    result = application_config.discover_application_config(
        downloads_dir=tmp_path,
        application_number="P-254482",
        model_workbook_application_number="P-254471",
    )

    assert result.application_number == "P-254482"
    assert result.application_id == "254482"
    assert result.model_template_path == workbook
    assert result.model_workbook_application_number == "P-254471"
    assert result.expected_model_numbers == ("MODEL-482",)


def test_default_discovery_uses_latest_template_application(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "Supplier-P-254471_Template.xlsx").touch()
    workbook = tmp_path / "Supplier-P-254471.xlsx"
    workbook.touch()

    monkeypatch.setattr(
        application_config,
        "_model_numbers",
        lambda workbook_path: ("MODEL-471",),
    )

    result = application_config.discover_application_config(
        downloads_dir=tmp_path,
    )

    assert result.application_number == "P-254471"
    assert result.application_id == "254471"
    assert result.model_template_path == workbook
    assert result.expected_model_number == "MODEL-471"


def test_explicit_application_number_must_match_supported_format(
    tmp_path,
) -> None:
    with pytest.raises(ValueError, match="P-<digits>"):
        application_config.discover_application_config(
            downloads_dir=tmp_path,
            application_number="254470",
        )


def test_explicit_application_without_workbook_has_actionable_error(
    tmp_path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Download or copy the populated workbook",
    ):
        application_config.discover_application_config(
            downloads_dir=tmp_path,
            application_number="P-254470",
        )


def test_model_number_reader_skips_template_placeholders(tmp_path) -> None:
    workbook = tmp_path / "Supplier-P-254472.xlsx"
    _write_workbook_with_model_numbers(
        workbook,
        ("Suffix", "Key", "MODEL-472"),
    )

    assert application_config._model_numbers(workbook) == ("MODEL-472",)


def test_model_number_reader_rejects_template_without_real_model_numbers(
    tmp_path,
) -> None:
    workbook = tmp_path / "Supplier-P-254473.xlsx"
    _write_workbook_with_model_numbers(workbook, ("Suffix", "Key"))

    with pytest.raises(ValueError, match="blank template"):
        application_config._model_numbers(workbook)

