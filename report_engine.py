import json, importlib, os
from reportlab.pdfgen import canvas


def load_config():
    with open("reports_config.json") as f:
        return json.load(f)


def load_data(path):
    with open(path) as f:
        return json.load(f)


def main(report_type, input_path, occasion, output_path):
    cfg = load_config()[report_type]
    data = load_data(input_path)

    # Basic validation against the schema stub. Only check top-level keys.
    schema = load_data(cfg["schema"])
    missing = [k for k in schema.keys() if k not in data]
    if missing:
        raise KeyError(f"Missing keys for {report_type}: {missing}")

    prompts_module = importlib.import_module(
        f"src.prompts.{report_type}.prompt_definitions_{report_type}"
    )
    c = canvas.Canvas(output_path)
    for section in prompts_module.SECTIONS:
        prompt = prompts_module.get_prompt(section, data, occasion)
        # 1) call OpenAI API with prompt → text
        # 2) c.drawString(...) or advanced layout
        c.showPage()
    c.save()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--type", required=True, choices=["numerology", "destiny_matrix", "astrocartography"])
    p.add_argument("--input", required=True)
    p.add_argument("--occasion", required=True, choices=["self_discovery", "gift"])
    p.add_argument("--output", required=True)
    args = p.parse_args()
    main(args.type, args.input, args.occasion, args.output)
