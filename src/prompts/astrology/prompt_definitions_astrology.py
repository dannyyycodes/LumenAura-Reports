SECTIONS = [
  "Sun Sign",
  "Moon Sign",
  "Rising Sign",
  "Mercury Placement",
  "Venus Placement",
  "Mars Placement",
  "Aspects Overview",
  "House Highlights"
]

def get_prompt(section, data, occasion):
    return (
      f"Astrology Report – {section}\n"
      f"Name: {data['name']}\n"
      f"Birth: {data['date_of_birth']} at {data['birth_time']} in {data['place_of_birth']}\n"
      f"Occasion: {occasion}\n\n"
      f"[AI Expansion Point: Provide a deep, insightful analysis of the {section} based on the chart data above.]"
    )
