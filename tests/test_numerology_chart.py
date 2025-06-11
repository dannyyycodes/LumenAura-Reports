from generate_numerology import generate_numerology_chart
import os

def test_chart_creation(tmp_path):
    # Given some sample numbers
    data = {'Destiny': 7, 'Soul Urge': 2, 'Expression': 5}
    out = tmp_path / "chart.png"
    # When we generate the chart
    generate_numerology_chart(data, str(out))
    # Then the file should exist and not be empty
    assert out.exists(), "Chart file was not created"
    assert out.stat().st_size > 0, "Chart file is empty"
