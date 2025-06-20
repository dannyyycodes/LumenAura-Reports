import json, os, importlib
from reportlab.pdfgen import canvas
import openai


def load_config():
    with open("reports_config.json") as f:
        return json.load(f)


def load_data(path):
    with open(path) as f:
        return json.load(f)


def validate_data(report_type, data):
    cfg = load_config()[report_type]
    with open(cfg["schema"]) as f:
        schema = json.load(f)
    missing = [k for k in schema.keys() if k not in data]
    if missing:
        raise KeyError(f"Missing keys for {report_type}: {missing}")


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


