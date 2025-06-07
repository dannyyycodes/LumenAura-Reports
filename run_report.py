import argparse
from report_engine import main

REPORT_TYPES = ["numerology", "destiny_matrix", "astrocartography", "astrology"]

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--type", required=True, choices=REPORT_TYPES)
    p.add_argument("--input", required=True)
    p.add_argument("--occasion", default="self_discovery")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    main(args.type, args.input, args.occasion, args.output)
