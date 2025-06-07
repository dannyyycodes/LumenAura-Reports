SECTIONS = ["destiny_matrix"]

PROMPT_TEMPLATES = {
    "destiny_matrix": (
        "Create a short Destiny Matrix overview for {name}. "
        "Life Path {life_path_number}, Challenges {challenge_numbers}, "
        "Innate Talent {innate_talent_number}, Balance {balance_number}."
    )
}

def get_prompt(section, data, occasion):
    template = PROMPT_TEMPLATES[section]
    return (
        template.format(
            name=data["name"],
            life_path_number=data["life_path_number"],
            challenge_numbers=", ".join(map(str, data["challenge_numbers"])),
            innate_talent_number=data["innate_talent_number"],
            balance_number=data["balance_number"],
        )
        + f" Occasion: {occasion}"
    )
