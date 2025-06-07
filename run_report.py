import argparse
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'reports_config.json')


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_schema(schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_data(report_type, data):
    config = load_config()
    if report_type not in config:
        raise ValueError(f"Unknown report type: {report_type}")
    schema = load_schema(config[report_type]['schema'])
    missing = []
    for key, value in schema.items():
        if key not in data:
            missing.append(key)
        elif isinstance(value, dict):
            # shallow check for nested keys
            for subkey in value:
                if subkey not in data[key]:
                    missing.append(f"{key}.{subkey}")
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate reports")
    config = load_config()
    parser.add_argument('report_type', choices=list(config.keys()))
    parser.add_argument('data_file')
    parser.add_argument('--occasion', default='self_discovery')
    args = parser.parse_args(argv)

    with open(args.data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    validate_data(args.report_type, data)
    print(f"Validated {args.report_type} report for {data.get('name')}")


if __name__ == '__main__':
    main()
