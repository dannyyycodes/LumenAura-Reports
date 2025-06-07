import argparse
import json
from report_engine import main, load_config


def validate_data(report_type, data):
    cfg = load_config()[report_type]
    with open(cfg["schema"]) as f:
        schema = json.load(f)
    missing = [k for k in schema.keys() if k not in data]
    if missing:
        raise KeyError(f"Missing keys for {report_type}: {missing}")


def cli():
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, choices=list(config.keys()))
    parser.add_argument("--input", required=True)
    parser.add_argument("--occasion", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    main(args.type, args.input, args.occasion, args.output)


if __name__ == "__main__":
    cli()
