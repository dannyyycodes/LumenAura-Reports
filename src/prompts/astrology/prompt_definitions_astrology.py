SECTIONS = ["planetary_analysis"]

# Original prompt template from prompt_definitions.py for Planetary Analysis
PROMPT_TEMPLATES = {
    "planetary_analysis": (
        "Write a detailed Planetary Analysis for {client_name}, approximately 700 words total. Analyze each key celestial body individually (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron).\n\n"
        "1. Create a poetic subheader incorporating the planet, its sign, and house (e.g., **☉ The Sun in {sun_sign} (House {sun_house}) – Your Radiant Core**). Note if {planet_retrograde}.\n"
        "2. Begin by stating the planet's core archetype, drawing from the provided theme: '{planet_core_theme_json}'.\n"
        "3. Elaborate poetically on how the planet manifests in its sign, expanding on the provided interpretation: '{planet_sign_interp_json}'.\n"
        "4. Describe its influence in its house, expanding on the provided interpretation: '{planet_house_interp_json}'.\n"
        "5. Include the provided dignity interpretation if applicable: '{planet_dignity_interp_json}'.\n"
        "6. Briefly weave in the influence of its tightest major aspects. Refer to the provided list of all aspect interpretations and select 1-2 key ones relevant to this planet: {all_aspect_interps_json}.\n"
        "7. Conclude each planet's section with a short insight or reflection on its role in {client_name}'s unique life journey and potential.\n\n"
        "Maintain an insightful, empathetic, second-person ('you') voice throughout. Ensure seamless integration of the provided interpretations into a flowing narrative.\n\n"
        "# The prompt template below lists placeholders for each planet, ensure they match the new context keys\n"
        "**Begin with the Sun:**\n**☉ The Sun in {sun_sign} (House {sun_house}) {sun_retrograde} – Your Radiant Core**\nCore Theme: {sun_core_theme_json}.\nSign Meaning: {sun_sign_interp_json}.\nHouse Meaning: {sun_house_interp_json}.\nDignity: {sun_dignity_interp_json}.\n[Elaborate poetically, synthesizing these elements and relevant aspects from the provided list...]\n\n"
        "**☽ The Moon in {moon_sign} (House {moon_house}) {moon_retrograde} – Your Inner Sanctuary**\nCore Theme: {moon_core_theme_json}.\nSign Meaning: {moon_sign_interp_json}.\nHouse Meaning: {moon_house_interp_json}.\nDignity: {moon_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**☿ Mercury in {mercury_sign} (House {mercury_house}) {mercury_retrograde} – Your Mind's Messenger**\nCore Theme: {mercury_core_theme_json}.\nSign Meaning: {mercury_sign_interp_json}.\nHouse Meaning: {mercury_house_interp_json}.\nDignity: {mercury_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**♀ Venus in {venus_sign} (House {venus_house}) {venus_retrograde} – Your Heart's Desire**\nCore Theme: {venus_core_theme_json}.\nSign Meaning: {venus_sign_interp_json}.\nHouse Meaning: {venus_house_interp_json}.\nDignity: {venus_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**♂ Mars in {mars_sign} (House {mars_house}) {mars_retrograde} – Your Driving Force**\nCore Theme: {mars_core_theme_json}.\nSign Meaning: {mars_sign_interp_json}.\nHouse Meaning: {mars_house_interp_json}.\nDignity: {mars_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**♃ Jupiter in {jupiter_sign} (House {jupiter_house}) {jupiter_retrograde} – Your Path of Expansion**\nCore Theme: {jupiter_core_theme_json}.\nSign Meaning: {jupiter_sign_interp_json}.\nHouse Meaning: {jupiter_house_interp_json}.\nDignity: {jupiter_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**♄ Saturn in {saturn_sign} (House {saturn_house}) {saturn_retrograde} – Your Structure and Lessons**\nCore Theme: {saturn_core_theme_json}.\nSign Meaning: {saturn_sign_interp_json}.\nHouse Meaning: {saturn_house_interp_json}.\nDignity: {saturn_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**♅ Uranus in {uranus_sign} (House {uranus_house}) {uranus_retrograde} – Your Spark of Awakening**\nCore Theme: {uranus_core_theme_json}.\nSign Meaning: {uranus_sign_interp_json}.\nHouse Meaning: {uranus_house_interp_json}.\nDignity: {uranus_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**♆ Neptune in {neptune_sign} (House {neptune_house}) {neptune_retrograde} – Your Connection to Mystery**\nCore Theme: {neptune_core_theme_json}.\nSign Meaning: {neptune_sign_interp_json}.\nHouse Meaning: {neptune_house_interp_json}.\nDignity: {neptune_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "**♇ Pluto in {pluto_sign} (House {pluto_house}) {pluto_retrograde} – Your Power of Transformation**\nCore Theme: {pluto_core_theme_json}.\nSign Meaning: {pluto_sign_interp_json}.\nHouse Meaning: {pluto_house_interp_json}.\nDignity: {pluto_dignity_interp_json}.\n[Elaborate poetically...]\n\n"
        "** Chiron in {chiron_sign} (House {chiron_house}) {chiron_retrograde} – Your Wound and Wisdom**\nCore Theme: {chiron_core_theme_json}.\nSign Meaning: {chiron_sign_interp_json}.\nHouse Meaning: {chiron_house_interp_json}.\nDignity: {chiron_dignity_interp_json}.\n[Elaborate poetically...]\n"
    )
}


def get_prompt(section, data, occasion):
    template = PROMPT_TEMPLATES[section]
    return (
        f"{template}\n\n"
        f"Name: {data['name']}\n"
        f"Birth: {data['date_of_birth']} at {data['birth_time']} in {data['place_of_birth']}\n"
        f"Occasion: {occasion}\n"
    )
