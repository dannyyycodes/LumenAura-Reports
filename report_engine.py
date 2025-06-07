import json
import importlib
from reportlab.pdfgen import canvas
import openai
from run_report import validate_data


def load_config():
    with open("reports_config.json") as f:
        return json.load(f)


def load_data(path):
    with open(path) as f:
        return json.load(f)


def _call_openai(prompt):
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        # Fallback for offline testing
        return f"AI RESPONSE: {prompt[:60]}"


def main(report_type, input_path, occasion, output_path):
    cfg = load_config()[report_type]
    data = load_data(input_path)
    validate_data(report_type, data)

    prompts_module = importlib.import_module(
        f"src.prompts.{report_type}.prompt_definitions_{report_type}"
    )

    c = canvas.Canvas(output_path)
    for section in prompts_module.SECTIONS:
        prompt = prompts_module.get_prompt(section, data, occasion)
        text = _call_openai(prompt)
        y = 750
        for line in text.splitlines():
            c.drawString(50, y, line)
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
        c.showPage()
    c.save()


if __name__ == "__main__":
    import argparse

    cfg = load_config()
    p = argparse.ArgumentParser()
    p.add_argument("--type", required=True, choices=list(cfg.keys()))
    p.add_argument("--input", required=True)
    p.add_argument("--occasion", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    main(args.type, args.input, args.occasion, args.output)
