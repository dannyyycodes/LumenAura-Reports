import sys, os
# ensure project root is on sys.path so we can import our scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generate_numerology import generate_numerology_chart


def test_chart_creation(tmp_path):
    # Given some sample numbers
    data = {'Destiny': 7, 'Soul Urge': 2, 'Expression': 5}
    out = tmp_path / "chart.png"
    # When we generate the chart
    generate_numerology_chart(data, str(out))
    # Then the file should exist and not be empty
    assert out.exists(), "Chart file was not created"
    assert out.stat().st_size > 0, "Chart file is empty"
