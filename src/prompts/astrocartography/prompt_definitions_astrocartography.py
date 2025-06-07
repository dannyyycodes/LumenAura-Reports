SECTIONS = ["locations"]

PROMPT_TEMPLATES = {
    "locations": (
        "Write a brief astrocartography insight for {name} covering each place listed: {place_list}."
    )
}

def get_prompt(section, data, occasion):
    places = ", ".join(loc["place_name"] for loc in data.get("locations", []))
    template = PROMPT_TEMPLATES[section]
    return template.format(name=data["name"], place_list=places) + f" Occasion: {occasion}"
