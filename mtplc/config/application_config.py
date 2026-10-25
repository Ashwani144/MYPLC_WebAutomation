"""Discover the application and populated model workbook for an upload run."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree


APPLICATION_NUMBER_PATTERN = re.compile(r"P-(\d+)", re.IGNORECASE)
MODEL_NUMBER_HEADER = "model number"
SPREADSHEET_NAMESPACE = (
    "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
)


@dataclass(frozen=True)
class ApplicationConfig:
    """Application details discovered from the latest downloaded template."""

    application_number: str
    application_id: str
    model_template_path: Path
    model_workbook_application_number: str
    expected_model_numbers: tuple[str, ...]

    @property
    def expected_model_number(self) -> str:
        """Return the first workbook model for backward compatibility."""
        return self.expected_model_numbers[0]


def _excel_cell_text(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    value = cell.find(f"{SPREADSHEET_NAMESPACE}v")

    if cell.get("t") == "inlineStr":
        return "".join(
            text.text or ""
            for text in cell.findall(f".//{SPREADSHEET_NAMESPACE}t")
        ).strip()

    if value is None or value.text is None:
        return ""

    if cell.get("t") == "s":
        return shared_strings[int(value.text)].strip()

    return value.text.strip()


def _model_numbers(workbook_path: Path) -> tuple[str, ...]:
    """Read unique model numbers below the Model Number column header."""
    with ZipFile(workbook_path) as workbook:
        shared_strings: list[str] = []
        shared_strings_path = "xl/sharedStrings.xml"

        if shared_strings_path in workbook.namelist():
            shared_strings_xml = ElementTree.fromstring(
                workbook.read(shared_strings_path)
            )
            shared_strings = [
                "".join(
                    text.text or ""
                    for text in item.findall(f".//{SPREADSHEET_NAMESPACE}t")
                )
                for item in shared_strings_xml.findall(
                    f"{SPREADSHEET_NAMESPACE}si"
                )
            ]

        worksheet = ElementTree.fromstring(
            workbook.read("xl/worksheets/sheet1.xml")
        )

    model_number_column: str | None = None
    model_number_header_row: int | None = None
    rows = worksheet.findall(
        f".//{SPREADSHEET_NAMESPACE}sheetData/"
        f"{SPREADSHEET_NAMESPACE}row"
    )

    for row_index, row in enumerate(rows):
        for cell in row.findall(f"{SPREADSHEET_NAMESPACE}c"):
            if _excel_cell_text(cell, shared_strings).casefold() == (
                MODEL_NUMBER_HEADER
            ):
                cell_reference = cell.get("r", "")
                column = re.match(r"[A-Z]+", cell_reference, re.IGNORECASE)

                if column is not None:
                    model_number_column = column.group()
                    model_number_header_row = row_index
                    break

        if model_number_column is not None:
            break

    if model_number_column is not None and model_number_header_row is not None:
        model_numbers: list[str] = []
        for row in rows[model_number_header_row + 1 :]:
            for cell in row.findall(f"{SPREADSHEET_NAMESPACE}c"):
                if re.match(
                    rf"^{re.escape(model_number_column)}\d+$",
                    cell.get("r", ""),
                    re.IGNORECASE,
                ):
                    model_number = _excel_cell_text(cell, shared_strings)
                    if model_number.casefold() == "section footer":
                        break
                    if model_number and model_number.casefold() not in {
                        "suffix",
                        "key",
                    }:
                        model_numbers.append(model_number)
            else:
                continue
            break

        if model_numbers:
            return tuple(dict.fromkeys(model_numbers))

    raise ValueError(
        f"No model number was found beneath the 'Model Number' column "
        f"in the first worksheet of '{workbook_path}'. "
        "This may be a blank template containing only Suffix/Key placeholders. "
        "Select the populated application workbook."
    )

def discover_application_config(
    downloads_dir: Path | None = None,
    application_number: str | None = None,
    model_workbook_application_number: str | None = None,
) -> ApplicationConfig:
    """Resolve a target application and its populated model workbook."""
    downloads = downloads_dir or Path.home() / "Downloads"

    if not downloads.is_dir():
        raise FileNotFoundError(
            f"Downloads folder does not exist: '{downloads}'."
        )

    latest_template_name: str | None = None

    if application_number is not None:
        application_match = APPLICATION_NUMBER_PATTERN.fullmatch(
            application_number.strip()
        )
        if application_match is None:
            raise ValueError(
                "Application number must use the format 'P-<digits>', "
                f"not '{application_number}'."
            )
        application_id = application_match.group(1)
    else:
        templates = [
            path
            for path in downloads.iterdir()
            if path.is_file()
            and path.suffix.casefold() == ".xlsx"
            and "_template" in path.stem.casefold()
            and APPLICATION_NUMBER_PATTERN.search(path.name) is not None
        ]

        if not templates:
            raise FileNotFoundError(
                f"No Excel template with an application number was found in "
                f"'{downloads}'. Expected a name such as "
                "'Company-P-255860_Template.xlsx'."
            )

        latest_modified = max(path.stat().st_mtime_ns for path in templates)
        latest_templates = [
            path
            for path in templates
            if path.stat().st_mtime_ns == latest_modified
        ]
        latest_application_numbers = {
            APPLICATION_NUMBER_PATTERN.search(path.name).group(1)
            for path in latest_templates
            if APPLICATION_NUMBER_PATTERN.search(path.name) is not None
        }
        latest_template_name = latest_templates[0].name

        if len(latest_application_numbers) != 1:
            names = ", ".join(sorted(path.name for path in latest_templates))
            raise ValueError(
                "The newest application templates are tied across different "
                f"application numbers: {names}. Update/download one target "
                "template again, then rerun the command."
            )

        application_id = latest_application_numbers.pop()

    application_number = f"P-{application_id}"
    workbook_application_id = application_id
    if model_workbook_application_number is not None:
        workbook_match = APPLICATION_NUMBER_PATTERN.fullmatch(
            model_workbook_application_number.strip()
        )
        if workbook_match is None:
            raise ValueError(
                "Model workbook application number must use the format "
                f"'P-<digits>', not '{model_workbook_application_number}'."
            )
        workbook_application_id = workbook_match.group(1)

    workbook_application_number = f"P-{workbook_application_id}"
    matching_workbooks = [
        path
        for path in downloads.iterdir()
        if path.is_file()
        and path.suffix.casefold() == ".xlsx"
        and "_template" not in path.stem.casefold()
        and any(
            match.group(1) == workbook_application_id
            for match in APPLICATION_NUMBER_PATTERN.finditer(path.name)
        )
    ]

    exact_name = re.compile(
        rf"(?:^|[-_])P-{re.escape(workbook_application_id)}$",
        re.IGNORECASE,
    )
    exact_workbooks = [
        path for path in matching_workbooks if exact_name.search(path.stem)
    ]
    candidates = exact_workbooks or matching_workbooks

    if len(candidates) != 1:
        names = ", ".join(sorted(path.name for path in candidates))
        if not candidates:
            if latest_template_name is None:
                raise FileNotFoundError(
                    f"No populated .xlsx workbook matching "
                    f"{workbook_application_number} was found in '{downloads}' "
                    f"for target application {application_number}. "
                    "Download or copy the populated workbook for this "
                    "application into Downloads. It should include the "
                    f"workbook application number in its name (for example, "
                    f"Company-{workbook_application_number}.xlsx) and must "
                    "not be the blank _Template.xlsx file."
                )
            raise FileNotFoundError(
                f"No populated .xlsx workbook matching "
                f"{workbook_application_number} was found in '{downloads}' "
                f"for target application {application_number}. The newest "
                f"matching template is '{latest_template_name}'. Save the "
                "populated workbook separately; do not rename the blank "
                "_Template.xlsx file."
            )
        raise ValueError(
            f"More than one populated workbook matches "
            f"{workbook_application_number}: "
            f"{names}. Keep one unambiguous workbook for that application "
            "or remove/rename old versions, then rerun the command."
        )

    model_template_path = candidates[0]
    expected_model_numbers = _model_numbers(model_template_path)

    return ApplicationConfig(
        application_number=application_number,
        application_id=application_id,
        model_template_path=model_template_path,
        model_workbook_application_number=workbook_application_number,
        expected_model_numbers=expected_model_numbers,
    )

