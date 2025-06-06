# format_report_content
import re


def format_planetary_section(raw_text):
    lines = raw_text.strip().split("\n")
    formatted = []
    buffer = []
    current_title = None

    for line in lines:
        line = line.strip()
        if line.startswith("**") and line.endswith("**"):
            if current_title and buffer:
                formatted.append(
                    {
                        "type": "section",
                        "title": current_title,
                        "content": "\n".join(buffer).strip(),
                    }
                )
                buffer = []
            current_title = re.sub(r"\*\*", "", line)
        elif line:
            buffer.append(line)

    if current_title and buffer:
        formatted.append(
            {
                "type": "section",
                "title": current_title,
                "content": "\n".join(buffer).strip(),
            }
        )

    return formatted
