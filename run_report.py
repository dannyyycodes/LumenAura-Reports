# run_report.py

import argparse
from report_engine import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate reports")
    parser.add_argument(
        "--type",
        required=True,
        choices=["numerology", "destiny_matrix", "astrocartography", "astrology"],
        help="Which report to generate",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the JSON data file",
    )
    parser.add_argument(
        "--occasion",
        default="self_discovery",
        choices=["self_discovery", "gift"],
        help="Report occasion context",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the generated PDF",
    )
    args = parser.parse_args()
    main(args.type, args.input, args.occasion, args.output)

