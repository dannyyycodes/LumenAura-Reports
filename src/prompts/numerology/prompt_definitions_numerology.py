"""Prompt helper for numerology reports."""

def get_prompt(section, data, occasion):
    """Return the text prompt for a numerology report section."""
    return (
        f"Numerology Report – {section}\n"
        f"Name: {data['name']}\n"
        f"Date of Birth: {data['date_of_birth']}\n"
        f"Occasion: {occasion}\n\n"
        f"[AI Expansion Point: Please provide an insightful analysis of the {section} based on the data above.]"
    )
