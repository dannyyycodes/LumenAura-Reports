import json
import os
import importlib.util
import pytest

spec = importlib.util.spec_from_file_location(
    "run_report",
    os.path.join(os.path.dirname(__file__), os.pardir, "run_report.py")
)
run_report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_report)
validate_data = run_report.validate_data

VALID_SAMPLES = {
    "astrology": "tests/samples/astrology_valid.json",
}

MISSING_SAMPLES = {
    "astrology": "tests/samples/astrology_missing.json",
}

@pytest.mark.parametrize("report_type, path", VALID_SAMPLES.items())
def test_valid_reports(report_type, path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    validate_data(report_type, data)

@pytest.mark.parametrize("report_type, path", MISSING_SAMPLES.items())
def test_missing_reports(report_type, path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with pytest.raises(ValueError):
        validate_data(report_type, data)
