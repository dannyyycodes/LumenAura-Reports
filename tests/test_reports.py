import pytest, os
from report_engine import main

@pytest.mark.parametrize("rtype,sample", [
    ("numerology", "tests/samples/numerology_valid.json"),
    ("destiny_matrix", "tests/samples/destiny_matrix_valid.json"),
    ("astrocartography", "tests/samples/astrocartography_valid.json"),
    ("astrology", "tests/samples/astrology_valid.json"),
])
def test_valid_report(tmp_path, rtype, sample):
    out = tmp_path / f"{rtype}.pdf"
    main(rtype, sample, "self_discovery", str(out))
    assert out.exists() and out.stat().st_size > 0

@pytest.mark.parametrize("rtype,sample", [
    ("numerology", "tests/samples/numerology_missing.json"),
    ("destiny_matrix", "tests/samples/destiny_matrix_missing.json"),
    ("astrocartography", "tests/samples/astrocartography_missing.json"),
    ("astrology", "tests/samples/astrology_missing.json"),
])
def test_missing_field(tmp_path, rtype, sample):
    with pytest.raises(Exception):
        main(rtype, sample, "gift", str(tmp_path / "fail.pdf"))
