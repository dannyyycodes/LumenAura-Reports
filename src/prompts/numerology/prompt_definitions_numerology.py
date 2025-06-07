SECTIONS = ["numerology"]

# Original prompt template from prompt_definitions.py for Numerology section
PROMPT_TEMPLATES = {
    "numerology": (
        "In 450 words, weave together the numerological significance for {client_name}:\n"
        "1. **Life Path {life_path_num}:** Elaborate on their core journey and purpose using the provided interpretation: '{lp_interp_json}'.\n"
        "2. **Personal Year {personal_year_num}:** Describe the theme and focus for their current annual cycle based on the provided interpretation: '{py_interp_json}'.\n"
        "3. **Soul Urge {soul_urge_num}:** Reveal their inner drive and heart's desire, expanding on the provided interpretation: '{su_interp_json}'. (If number is '?', briefly state name wasn't provided for calculation).\n"
        "4. **Expression {expression_num}:** Describe their potential talents and path of outward expression using the provided interpretation: '{ex_interp_json}'. (If number is '?', briefly state name wasn't provided for calculation).\n"
        "Connect these threads to show how their numerical signature influences their path."
    )
}


def get_prompt(section, data, occasion):
    template = PROMPT_TEMPLATES[section]
    return (
        f"{template}\n\n"
        f"Name: {data['name']}\n"
        f"Date of Birth: {data['date_of_birth']}\n"
        f"Occasion: {occasion}\n"
    )

