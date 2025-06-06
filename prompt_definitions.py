# prompt_definitions.py
# Contains the prompt structures for the astrology report.
# --- VERSION 1.4: Renamed PROMPTS to HUMAN_PROMPTS ---
# --- VERSION 1.3: Updated prompts to use JSON interpretation context keys and removed section 99 ---
# --- Cleaned non-breaking spaces (U+00A0) ---

# <<< RENAMED VARIABLE FROM PROMPTS to HUMAN_PROMPTS >>>
HUMAN_PROMPTS = {
    "00_Cover_Page": {
        "header": "Cosmic Blueprint",
        "quote": "",
        "static_intro": "",
        "ai_prompt": "",
        "word_count": 0,
        "meta": {"skip_ai": True}
    },

    "01_Mythic_Prologue": {
        "header": "Mythic Prologue",
        "quote": "“The cosmos is within us. We are made of star-stuff. We are a way for the universe to know itself.” — Carl Sagan",
        "static_intro": (
            "The universe paused on the threshold of your birth. Galaxies tilted their gaze as your first breath became a ripple in the cosmic loom.\n\n"
            "Your Sun and Rising signs are not passive symbols—they are gateways through which ancient myths step into flesh. What stellar hands sculpted your hour of arrival? What epic waits in the margins of your chart? The stars lean closer. Begin."
        ),
        # --- Updated prompt to use JSON context keys ---
        "ai_prompt": (
            "Building on the introduction above, continue in the same second-person oracle voice and write a 300-word prologue for {client_name} in three paragraphs.\n\n"
            "Paragraph 1 (Origin): Reference Sun in {sun_sign} (Interpretation: {sun_sign_interp_json}) and Rising in {asc_sign} (Interpretation: {asc_sign_interp_json}) as mythic portals into their life story.\n" # Use JSON
            "Paragraph 2 (Archetype Power): Highlight Chart Ruler {chart_ruler_planet} in House {chart_ruler_house} (Interpretation: {chart_ruler_interp_json}), the tightest aspect {tightest_aspect_str} as a hidden superpower, and link dominant element {dominant_element} (Interpretation: {dom_elem_interp_json}) to their mythic identity.\n" # Use JSON
            "Paragraph 3 (Mantra): Sync their age ({age}) with current life phase ({current_transit_phase}) and close with a poetic power mantra."
        ),
        "word_count": 300,
        "meta": {
            "tone_mode": "intro",
            "tactics": ["Narrative Transport", "Mythic Framing"],
            "theme": "Soul Hero"
        }
    },
    "02_Client_Details": {
        "header": "Your Cosmic Signature",
        "quote": "“Coordinates are spells.” — Astrologer’s Aphorism",
        "static_intro": (
            "Coordinates are spells. Your birth time, place, and date form a sigil etched in "
            "spacetime—a quantum fingerprint. Below is your personal chart data: the raw metrics "
            "that ground everything that follows, providing a stable foundation for deeper insights."
        ),
        "ai_prompt": "", # This section uses a data table, not AI
        "word_count": 0,
        "meta": {"skip_ai": True} # Handled by table logic
    },

    "03_Earth_Energies": {
        "header": "Earth Energies",
        "quote": "“The earth has music for those who listen.” — George Santayana",
        "static_intro": (
            "Earth is alive in jagged mountain peaks, ocean tides, desert sands, and hidden crystal veins glowing beneath your feet. "
            "We all share this beautiful ecosystem, living symbiotically in a web of life that nourishes and sustains us all. "
            "Underfoot, quartz and amethyst pulses mix with threads of gold humming with ancient power, tracing energy lines that link canyons, "
            "forests, and sacred stone circles. Invisible pathways—formed by sky winds, river currents, and rooted forests—pulse with the planet’s "
            "life force, guiding the flow of energy across every landscape. At the moment you were born, the minerals beneath your unique birthplace, "
            "the sun’s daily arc, and the moon’s gentle tug wove a one‑of‑a‑kind resonance into your cells. In the sections ahead, you’ll explore "
            "grounding rituals, elemental practices, and crystal‑infused exercises that tune you to Earth’s living energy lines, awaken your inner "
            "strength, and guide each step with the planet’s vibrant heartbeat."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "You’re an astro‑somatic guide. In 500 words, craft an Earth Energies section for {client_name} "
            "that weaves sensory imagery, scientific insight, and hands‑on practice. Use these exact HTML‑bold subheaders (no Markdown):\n\n"

            "<b>Schumann Resonance Connection:</b> Describe {schumann_resonance} and lead a simple breath‑or‑tone exercise syncing with Earth’s heartbeat.\n\n"

            "<b>Crystal Veins & Ley Lines:</b> Detail how subterranean mineral currents—quartz, amethyst, and gold threads—flow beneath {birth_location} "
            "in the {hemisphere}. Then guide a crystal‑grid mapping practice: place three paired stones at the east, south, and west points around your "
            "home or outdoor altar to form your personal energy network.\n\n"

            "<b>Moon Phase Resonance:</b> Tie {moon_phase_name} to mood and physiology, using the provided interpretation {moon_phase_interp_json}, and offer a moon‑phase ritual for emotional alignment.\n\n" # Use JSON for moon phase

            "<b>Elemental Grounding:</b> Based on their elemental balance ({elemental_balance_str}), suggest specific tactile, olfactory, or movement exercises that connect them to their dominant element ({dominant_element}) and help integrate their weakest element ({weakest_element}). Use the provided interpretation for their dominant elemental combination {dominant_combo_interp_json}. Briefly mention the core themes of these elements (Dominant: {dominant_element_themes_json} / Weakest: {weakest_element_themes_json}).\n\n" # Use JSON for dominant combo and themes

            "<b>Earthing Practice:</b> Invite barefoot walking on natural ground for 5–10 minutes daily to absorb Earth’s electrons and reduce stress.\n\n"

            "<b>Forest Bathing:</b> Guide a mindful stroll in green spaces—focus on senses to lower cortisol and deepen kinship with the land.\n\n"

            "<b>Herbal Allies:</b> Recommend local grounding teas (e.g., nettle, dandelion) or tinctures for an earth‑rooted ritual.\n\n"

            "<b>Earth‑Bound Nutrition:</b> Suggest a seasonal, plant‑based snack or meal that echoes the elemental focus—think roasted root veggies in autumn or fresh spring greens with wild herbs.\n\n"

            "Seamlessly integrate at least two of these psychological techniques: Narrative Transport, Somatic Markers, Peak‑End Rule, Framing Effect, Self‑Perception Theory, Choice Architecture.\n\n"

            "Use every placeholder exactly as written—do not rename, omit, or paraphrase tokens."
        ),
        "word_count": 500,
        "meta": {
            "tone_mode": "ritual",
            "tactics": ["Somatic Markers", "Peak-End Rule"],
            "theme": "Earthwalker"
        }
    },

    "04_Fixed_Stars_Constellations": {
        "header": "Fixed Stars & Constellations",
        "quote": "“The stars incline; they do not compel.” — Ptolemy",
        "static_intro": (
            "The Milky Way is your ancestral lineage. Sirius, Aldebaran, Regulus, and Vega beam ancestral memories "
            "into your chart, linking you to ancient temples and mythic legacies."
        ),
        # <<< Prompt uses structured JSON already, needs slight adjustment >>>
        "ai_prompt": (
            "Below is JSON data listing significant fixed stars conjunct key points in {client_name}'s chart. Interpret this cosmic lineage in approx 550 words, weaving a narrative about their stellar connections:\n\n"
            "For **each star object** within the provided JSON list (Interpretation is provided in the 'brief_interpretation' and 'mythology_link' fields within each object):\n" # Added clarification
            "1. Identify the star (`star_name`), the aligned planet/point (`linked_planet`), and the closeness of the alignment (`orb_degrees`). Note the star's position: {star_sign} {star_exact_degree}° in House {star_house}.\n"
            "2. Drawing deep inspiration from its core essence (`star_keywords`) and considering its prominence (`star_magnitude`), poetically describe the star's archetypal energy. Elaborate on the `star_brief_interpretation` provided in the JSON, exploring its potential influence (both gifts and challenges) on {client_name}'s path, particularly through the lens of the `{linked_planet}` it touches.\n" # Explicitly mention using provided interp
            "3. Briefly connect the star's themes to the provided `star_mythology_link`, creating a sense of ancestral resonance.\n\n"
            "If the provided JSON list is empty (`[]`), write a brief, reflective paragraph stating: 'Your cosmic signature doesn't show strong alignments with the most prominent fixed stars within the standard orb. This suggests your unique path unfolds primarily through the dynamic interplay of the planets and houses in your chart, granting you a certain freedom from overriding stellar destinies. Your focus lies in mastering the planetary energies discussed throughout this blueprint.'\n\n"
            "Maintain an insightful, mythic, second-person voice throughout.\n\n"
            "**JSON Data:**\n{structured_fixed_star_data_json}" # Use the structured JSON context key
        ),
        "word_count": 550,
        "meta": {
            "tone_mode": "karmic",
            "tactics": ["Ancestral Resonance", "Symbolic Mapping"],
            "theme": "Stellar Lineage"
        }
    },

    "05_Core_Essence": {
        "header": "Core Essence",
        "quote": "“The soul always knows what to do to heal itself. The challenge is to silence the mind.” — Caroline Myss",
        "static_intro": (
            "Beneath the noise of roles and routines hums your soul’s tuning fork. Its vibration threads through your chart via "
            "the chart ruler, the untouched planets, and elemental blends to reveal your irreducible self."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "In 250 words, reveal {client_name}’s core essence by weaving together these threads:\n"
            "1. The Chart Ruler {chart_ruler_planet} in House {chart_ruler_house}. Use the provided interpretation: '{chart_ruler_interp_json}'.\n" # Use JSON
            "2. Any unaspected planets ({unaspected_planets_str}). Refer to the provided list of unaspected planet interpretations: {unaspected_interps_json}. Describe them as pure, perhaps latent, archetypal powers needing conscious integration.\n" # Use JSON list
            "3. The interplay between the Sun ({sun_sign}) and Ascendant ({asc_sign}) as the balance between inner vitality and outer projection. Use the provided interpretations: Sun - '{sun_sign_interp_json}', Ascendant - '{asc_sign_interp_json}'.\n" # Use JSON
            "4. How their dominant modality ({dominant_modality}), shapes their fundamental rhythm and approach to life. Use the provided interpretation for their dominant modality: '{dom_mod_interp_json}'.\n" # Use JSON
            "5. Briefly discuss any insights from the provided list of Midpoint interpretations: {midpoint_interps_json}.\n" # Reference JSON list for midpoints
            "6. Briefly discuss any insights from the provided list of Aspect Pattern interpretations: {aspect_pattern_interps_json}.\n" # Reference JSON list for patterns
            "7. Weave these together, suggesting how these inner figures interact. Conclude with the closing question: “Which archetypal voice within you will you consciously amplify now?”"
        ),
        "word_count": 250,
        "meta": {
            "tone_mode": "reflective", # Changed from default based on Task 4 plan
            "tactics": ["Self-Perception Theory", "Inner Mirror Anchoring"], # Changed from default based on Task 4 plan
            "theme": "Sacred Self" # Changed from default based on Task 4 plan
        }
    },

    "06_Elemental_Chakras": {
        "header": "Elemental Chakras",
        "quote": "“The body is the temple of the soul, and each chakra a throne of light.” — Tantric Sutra",
        "static_intro": (
            "Your spine is a ladder of elements: Fire at the solar plexus, Water at the sacral, Air at the heart, Earth at the root, Ether at the crown. Balance is not the goal—harmony is."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "You’re an astro‑somatic guide. In 500 words, craft an Earth Energies section for {client_name} " # Note: Reusing Earth Energies prompt structure as base per previous versions
            "that weaves sensory imagery, scientific insight, and hands‑on practice. Use these exact HTML‑bold subheaders (no Markdown):\n\n"

            "<b>Schumann Resonance Connection:</b> Describe {schumann_resonance} and lead a simple breath‑or‑tone exercise syncing with Earth’s heartbeat.\n\n"

            "<b>Crystal Veins & Ley Lines:</b> Detail how subterranean mineral currents—quartz, amethyst, and gold threads—flow beneath {birth_location} "
            "in the {hemisphere}. Then guide a crystal‑grid mapping practice: place three paired stones at the east, south, and west points around your "
            "home or outdoor altar to form your personal energy network.\n\n"

            "<b>Moon Phase Resonance:</b> Tie {moon_phase_name} to mood and physiology, using the provided interpretation {moon_phase_interp_json}, and offer a moon‑phase ritual for emotional alignment.\n\n" # Use JSON for moon phase

            "<b>Elemental Grounding:</b> Based on their elemental balance ({elemental_balance_str}), suggest specific tactile, olfactory, or movement exercises that connect them to their dominant element ({dominant_element}) and help integrate their weakest element ({weakest_element}). Use the provided interpretation for their dominant elemental combination {dominant_combo_interp_json}. Briefly mention the core themes of these elements (Dominant: {dominant_element_themes_json} / Weakest: {weakest_element_themes_json}).\n\n" # Use JSON for dominant combo and themes

            "<b>Earthing Practice:</b> Invite barefoot walking on natural ground for 5–10 minutes daily to absorb Earth’s electrons and reduce stress.\n\n"

            "<b>Forest Bathing:</b> Guide a mindful stroll in green spaces—focus on senses to lower cortisol and deepen kinship with the land.\n\n"

            "<b>Herbal Allies:</b> Recommend local grounding teas (e.g., nettle, dandelion) or tinctures for an earth‑rooted ritual.\n\n"

            "<b>Earth‑Bound Nutrition:</b> Suggest a seasonal, plant‑based snack or meal that echoes the elemental focus—think roasted root veggies in autumn or fresh spring greens with wild herbs.\n\n"

            "Seamlessly integrate at least two of these psychological techniques: Narrative Transport, Somatic Markers, Peak‑End Rule, Framing Effect, Self‑Perception Theory, Choice Architecture.\n\n"

            "Use every placeholder exactly as written—do not rename, omit, or paraphrase tokens."
        ),
        "word_count": 500,
        "meta": {
            "tone_mode": "ritual",
            "tactics": ["Somatic Markers", "Peak-End Rule"],
            "theme": "Earthwalker"
        }
    },

    "06b_Modality_Balance": {
        "header": "Modality Balance",
        "quote": "“To move, to shape, to transform — the rhythm of your chart is your becoming.” — Esoteric Astrology Codex",
        "static_intro": (
            "Cardinal sparks action, Fixed sustains energy, Mutable adapts flow. Your modality distribution ({modality_balance_str}) is the rhythm of your becoming."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "In 350 words, analyze {client_name}'s modality balance ({modality_balance_str}):\n"
            "1. Identify their dominant modality ({dominant_modality}) and discuss its core themes ({dominant_modality_themes_json}). Elaborate on its influence based on the provided interpretation: '{dom_mod_interp_json}'.\n" # Use JSON for theme and interp
            "2. Discuss how this dominant rhythm shapes their approach to emotional cycles and creative processes.\n"
            "3. Identify their weakest modality ({weakest_modality}) and briefly reflect on its implications based on the provided interpretation: '{weak_mod_interp_json}'. Discuss how this might manifest in their life.\n" # Use JSON for interp
            "4. Use a vivid metaphor to describe their overall modality rhythm."
        ),
        "word_count": 350,
        "meta": {
            "tone_mode": "reflective", # Changed from default based on Task 4 plan
            "tactics": ["Self-Perception Theory", "Inner Mirror Anchoring"], # Changed from default based on Task 4 plan
            "theme": "Sacred Self" # Changed from default based on Task 4 plan
        }
    },

    "07_Numerology": {
        "header": "Numerology",
        "quote": "“Numbers are the secret language of the universe.” — Pythagoras",
        "static_intro": (
            "Your Life Path, Personal Year, Soul Urge, and Expression numbers form the fractal equations of your soul’s journey."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "In 450 words, weave together the numerological significance for {client_name}:\n"
            "1. **Life Path {life_path_num}:** Elaborate on their core journey and purpose using the provided interpretation: '{lp_interp_json}'.\n" # Use JSON
            "2. **Personal Year {personal_year_num}:** Describe the theme and focus for their current annual cycle based on the provided interpretation: '{py_interp_json}'.\n" # Use JSON
            "3. **Soul Urge {soul_urge_num}:** Reveal their inner drive and heart's desire, expanding on the provided interpretation: '{su_interp_json}'. (If number is '?', briefly state name wasn't provided for calculation).\n" # Use JSON
            "4. **Expression {expression_num}:** Describe their potential talents and path of outward expression using the provided interpretation: '{ex_interp_json}'. (If number is '?', briefly state name wasn't provided for calculation).\n" # Use JSON
            "Connect these threads to show how their numerical signature influences their path."
        ),
        "word_count": 450,
        "meta": {
            "tone_mode": "technical", # Changed from default based on Task 4 plan
            "tactics": ["Narrative Transport", "Symbolic Mapping"], # Changed based on Task 4 plan
            "theme": "Numerical Code" # Changed based on Task 4 plan
        }
    },

    "08_Soul_Key": {
        "header": "Soul Key",
        "quote": "“The soul remembers what the mind forgets — your chart is its memory palace.”",
        "static_intro": (
            "Chiron, Saturn, and the lunar nodes trace the sacred math of your soul’s contracts and healing journey."
        ),
        # <<< Updated prompt to use JSON context keys and reference declination/pluto aspects lists >>>
        "ai_prompt": (
            "In 650 words, decode {client_name}’s Soul Key by synthesizing these core elements:\n"
            "1. **Chiron's Wound & Wisdom:** ({chiron_sign} / House {chiron_house}). Elaborate on the core wound described in the provided interpretations: Sign - '{chiron_sign_interp_json}' and House - '{chiron_house_interp_json}', focusing on how integrating this vulnerability ({chiron_core_theme_json}) becomes a source of wisdom and healing for self and others. Mention key aspects to Chiron, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Use JSON for Chiron, core theme, and reference aspects list
            "2. **Saturn's Karmic Lessons:** ({saturn_sign} / House {saturn_house}). Discuss the life area and manner ({saturn_core_theme_json}) where discipline, responsibility, and maturity are tested and forged. Expand on the provided interpretations: Sign - '{saturn_sign_interp_json}' and House - '{saturn_house_interp_json}'. Mention key aspects to Saturn, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Use JSON for Saturn, core theme, and reference aspects list
            "3. **The Nodal Axis Journey:** Describe the evolutionary pull from the South Node ({south_node_sign} / House {south_node_house}) comfort zone towards the North Node ({north_node_sign} / House {north_node_house}) path of growth. Weave together the interpretations for the sign path ('{north_node_sign_interp_json}') and the house path ('{north_node_house_interp_json}'). Also, consider the provided interpretations for the South Node sign ('{south_node_sign_interp_json}') and house ('{south_node_house_interp_json}') into a cohesive narrative of soul intention.\n" # Use JSON for Nodes
            "4. **Declination Insights:** Briefly incorporate insights from any notable declination aspects, referring to the provided list of declination aspect interpretations: {declination_aspect_interps_json}.\n" # Reference JSON list
            "5. **Pluto's Transformation:** Briefly mention how Pluto's major aspects ({pluto_aspects_str}) act as triggers for deep transformation and soul alchemy, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Reference JSON list (Pluto aspects string kept for backwards compat)
            "6. **Signature Facet:** Briefly reference the tightest aspect ({tightest_aspect_str}) as a defining characteristic woven into their soul's contract."
        ),
        "word_count": 650,
        "meta": {
            "tone_mode": "karmic",
            "tactics": ["Ancestral Resonance", "Symbolic Mapping"],
            "theme": "Stellar Lineage"
        }
    },

    "09_Planetary_Analysis": {
        "header": "Planetary Analysis",
        "quote": "“The night sky is a mirror—when you look up, you meet yourself in the stars.” — Ancient Hermetic Saying",
        "static_intro": (
            "The planets convene a council of inner selves—each sign, house, and aspect weaving your mythic and psychological tapestry."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "Write a detailed Planetary Analysis for {client_name}, approximately 700 words total. Analyze each key celestial body individually (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron).\n\n"
            "1. Create a poetic subheader incorporating the planet, its sign, and house (e.g., **☉ The Sun in {sun_sign} (House {sun_house}) – Your Radiant Core**). Note if {planet_retrograde}.\n"
            "2. Begin by stating the planet's core archetype, drawing from the provided theme: '{planet_core_theme_json}'.\n" # Use JSON for theme
            "3. Elaborate poetically on how the planet manifests in its sign, expanding on the provided interpretation: '{planet_sign_interp_json}'.\n" # Use JSON for sign
            "4. Describe its influence in its house, expanding on the provided interpretation: '{planet_house_interp_json}'.\n" # Use JSON for house
            "5. Include the provided dignity interpretation if applicable: '{planet_dignity_interp_json}'.\n" # Use JSON for dignity
            "6. Briefly weave in the influence of its tightest major aspects. Refer to the provided list of all aspect interpretations and select 1-2 key ones relevant to this planet: {all_aspect_interps_json}.\n" # Use JSON list for aspects
            "7. Conclude each planet's section with a short insight or reflection on its role in {client_name}'s unique life journey and potential.\n\n"
            "Maintain an insightful, empathetic, second-person ('you') voice throughout. Ensure seamless integration of the provided interpretations into a flowing narrative.\n\n"
            # The prompt template below lists placeholders for each planet, ensure they match the new context keys
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
        ),
        "word_count": 700, # May need adjustment
        "meta": {
            "tone_mode": "technical", # Changed from default based on Task 4 plan
            "tactics": ["Archetypal Reflection", "Narrative Transport"], # Changed based on Task 4 plan
            "theme": "Inner Pantheon" # Changed based on Task 4 plan
        }
    },

    "10_Celestial_Poetry": {
        "header": "Celestial Poetry",
        "quote": "“My soul is in the sky.” — William Shakespeare",
        "static_intro": (
            "Astrology as sonnet: planetary placements become verses of longing, hope, and mystery."
        ),
        # <<< Updated prompt to use JSON context keys and reference aspects/patterns lists >>>
        "ai_prompt": (
            "Create a 600‑word poetic meditation for {client_name} focusing on the dreamlike and spiritual nature of the chart.\n"
            "Weave in the essence of Neptune ({neptune_sign}, provided interpretation: {neptune_sign_interp_json}), Moon ({moon_sign}, provided interpretation: {moon_sign_interp_json}), and Venus ({venus_sign}, provided interpretation: {venus_sign_interp_json}).\n" # Use JSON for planet sign interp
            "Refer to the provided list of all aspect interpretations ({all_aspect_interps_json}) and aspect pattern interpretations ({aspect_pattern_interps_json}). Select key aspects and patterns that contribute to a sense of flow, mystery, or spiritual connection, and use their interpretations to enrich the poetry.\n" # Reference JSON lists
            "Use lyrical metaphors for each planet and the overall chart structure."
        ),
        "word_count": 600,
        "meta": {
            "tone_mode": "ritual", # Changed from default based on Task 4 plan
            "tactics": ["Mystic Framing", "Narrative Transport"], # Changed from default based on Task 4 plan
            "theme": "Celestial Harmony" # Changed from default based on Task 4 plan
        }
    },

    "11_Asteroid_Goddesses": {
        "header": "Asteroid Goddesses",
        "quote": "“The goddess doesn’t arrive — she awakens.” — Temple of Delphi Inscription",
        "static_intro": (
            "Ceres, Juno, Vesta, and Pallas Athena are divine emissaries of nurturing, contracts, devotion, and wisdom."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "Explore the influence of the four major asteroid goddesses in {client_name}'s chart, writing approximately 600 words total. Analyze each goddess individually:\n\n"
            "1. Create a subheader for each goddess (e.g., **Ceres: The Nurturing Principle**).\n"
            "2. State the goddess's core archetype based on the provided theme: '{asteroid_core_theme_json}'.\n" # Use JSON for theme
            "3. Describe how this archetype is expressed in her sign ({asteroid_sign}), expanding on the provided interpretation: '{asteroid_sign_interp_json}'.\n" # Use JSON for sign
            "4. Explain her influence within her house ({asteroid_house}), expanding on the provided interpretation: '{asteroid_house_interp_json}'. Note if {asteroid_retrograde}.\n" # Use JSON for house
            "5. Briefly mention 1-2 key aspects shaping her expression. Refer to the provided list of all aspect interpretations and select relevant ones: {all_aspect_interps_json}.\n" # Reference JSON list
            "6. Offer an insight into how this goddess archetype plays out in {client_name}'s modern life (e.g., relationships, work, self-care, strategy).\n\n"
            "Maintain an insightful, second-person voice.\n\n"
            # The prompt template lists placeholders for each asteroid, ensure they match the new context keys
            "**Ceres: The Nurturing Principle**\nPlacement: {ceres_sign} in House {ceres_house} {ceres_retrograde}.\nCore Archetype: {ceres_core_theme_json}.\nSign Expression: {ceres_sign_interp_json}.\nHouse Influence: {ceres_house_interp_json}.\n[Elaborate poetically on nurturing style, self-care needs, relationship to sustenance, synthesizing interpretations and relevant aspects...]\n\n"
            "**Pallas Athena: The Strategic Weaver**\nPlacement: {pallas_sign} in House {pallas_house} {pallas_retrograde}.\nCore Archetype: {pallas_core_theme_json}.\nSign Expression: {pallas_sign_interp_json}.\nHouse Influence: {pallas_house_interp_json}.\n[Elaborate poetically on wisdom style, pattern recognition, approach to problem-solving, synthesizing interpretations and relevant aspects...]\n\n"
            "**Juno: The Partner and Keeper of Contracts**\nPlacement: {juno_sign} in House {juno_house} {juno_retrograde}.\nCore Archetype: {juno_core_theme_json}.\nSign Expression: {juno_sign_interp_json}.\nHouse Influence: {juno_house_interp_json}.\n[Elaborate poetically on partnership needs, approach to commitment, relationship dynamics, synthesizing interpretations and relevant aspects...]\n\n"
            "**Vesta: The Sacred Flame Within**\nPlacement: {vesta_sign} in House {vesta_house} {vesta_retrograde}.\nCore Archetype: {vesta_core_theme_json}.\nSign Expression: {vesta_sign_interp_json}.\nHouse Influence: {vesta_house_interp_json}.\n[Elaborate poetically on devotion, focus, inner sanctuary, relationship to work/service, synthesizing interpretations and relevant aspects...]\n\n"
        ),
        "word_count": 600,
        "meta": {
            "tone_mode": "reflective", # Changed from default based on Task 4 plan
            "tactics": ["Archetypal Reflection", "Symbolic Mapping"], # Changed based on Task 4 plan
            "theme": "Inner Feminine" # Changed from default based on Task 4 plan
        }
    },

    "12_Karmic_Patterns": {
        "header": "Karmic Patterns",
        "quote": "“The soul remembers what the mind forgets — your chart is its memory palace.”",
        "static_intro": (
            "Chiron, Saturn, and the lunar nodes trace the sacred math of your soul’s contracts and healing journey."
        ),
        # <<< Updated prompt to use JSON context keys and reference declination/pluto aspects lists >>>
        "ai_prompt": (
            "In 650 words, decode {client_name}’s Soul Key by synthesizing these core elements:\n"
            "1. **Chiron's Wound & Wisdom:** ({chiron_sign} / House {chiron_house}). Elaborate on the core wound described in the provided interpretations: Sign - '{chiron_sign_interp_json}' and House - '{chiron_house_interp_json}', focusing on how integrating this vulnerability ({chiron_core_theme_json}) becomes a source of wisdom and healing for self and others. Mention key aspects to Chiron, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Use JSON for Chiron, core theme, and reference aspects list
            "2. **Saturn's Karmic Lessons:** ({saturn_sign} / House {saturn_house}). Discuss the life area and manner ({saturn_core_theme_json}) where discipline, responsibility, and maturity are tested and forged. Expand on the provided interpretations: Sign - '{saturn_sign_interp_json}' and House - '{saturn_house_interp_json}'. Mention key aspects to Saturn, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Use JSON for Saturn, core theme, and reference aspects list
            "3. **The Nodal Axis Journey:** Describe the evolutionary pull from the South Node ({south_node_sign} / House {south_node_house}) comfort zone towards the North Node ({north_node_sign} / House {north_node_house}) path of growth. Weave together the interpretations for the sign path ('{north_node_sign_interp_json}') and the house path ('{north_node_house_interp_json}'). Also, consider the provided interpretations for the South Node sign ('{south_node_sign_interp_json}') and house ('{south_node_house_interp_json}') into a cohesive narrative of soul intention.\n" # Use JSON for Nodes
            "4. **Declination Insights:** Briefly incorporate insights from any notable declination aspects, referring to the provided list of declination aspect interpretations: {declination_aspect_interps_json}.\n" # Reference JSON list
            "5. **Pluto's Transformation:** Briefly mention how Pluto's major aspects ({pluto_aspects_str}) act as triggers for deep transformation and soul alchemy, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Reference JSON list (Pluto aspects string kept for backwards compat)
            "6. **Signature Facet:** Briefly reference the tightest aspect ({tightest_aspect_str}) as a defining characteristic woven into their soul's contract."
        ),
        "word_count": 650,
        "meta": {
            "tone_mode": "karmic",
            "tactics": ["Ancestral Resonance", "Symbolic Mapping"],
            "theme": "Stellar Lineage"
        }
    },

    "13_Career_Wealth": {
        "header": "Career & Wealth",
        "quote": "“Your calling is not what you do — it’s where your soul becomes currency.” — Mystery School Scroll",
        "static_intro": (
            "Midheaven, second house, and sixth house placements map where vocation, values, and service intersect for abundance."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "Analyze the Career & Wealth blueprint for {client_name} (approx 600 words):\n"
            "1. **Midheaven (MC) - Your Calling:** Discuss the path to public achievement indicated by the MC in {mc_sign}. Elaborate on the approach suggested by the provided interpretation: '{house_10_sign_interp_json}'. Consider how key aspects to the Midheaven ({mc_aspects_str}) influence this path, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Use JSON for House 10 cusp and reference aspects list
            "2. **2nd House - Your Values & Resources:** Explore themes of self-worth and material security based on the 2nd House. Use the provided interpretation for the sign on the cusp ({house_2_cusp_sign}): '{house_2_sign_interp_json}'. Use the provided interpretation for the house themes: '{house_2_core_themes_json}'. Mention any planets residing here ({house_2_planets_str}) and their influence, referring to their provided planet in house interpretations from {all_planet_house_interps_json}.\n" # Use JSON for House 2 themes/cusp, and reference list for planets in house
            "3. **6th House - Your Work & Service:** Examine the approach to daily work, service, and well-being indicated by the 6th House. Use the provided interpretation for the sign on the cusp ({house_6_cusp_sign}): '{house_6_sign_interp_json}'. Use the provided interpretation for the house themes: '{house_6_core_themes_json}'. Note any planets activating this area ({house_6_planets_str}) and their influence, referring to their provided planet in house interpretations from {all_planet_house_interps_json}.\n" # Use JSON for House 6 themes/cusp, and reference list for planets in house
            "4. Synthesize these three areas, offering insight into how {client_name} might align vocation, values, and service for fulfilling abundance. Offer one related journal prompt."
        ),
        "word_count": 600,
        "meta": {
            "tone_mode": "technical", # Changed from default based on Task 4 plan
            "tactics": ["Future Visualization", "Value Framing"], # Changed based on Task 4 plan
            "theme": "Sacred Vocation" # Changed based on Task 4 plan
        }
    },

    "14_Love_Soulmates": {
        "header": "Love & Soulmates",
        "quote": "“The soulmate is not found — they are remembered.” — Theosophical Aphorism",
        "static_intro": (
            "Venus and the Descendant cast the blueprint for partnership and soul resonance."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "In 550 words, explore the landscape of Love & Soulmates for {client_name}:\n"
            "1. **Venus - Your Attraction Principle:** Analyze Venus in {venus_sign} (House {venus_house}). Use the provided interpretations: Sign - '{venus_sign_interp_json}' and House - '{venus_house_interp_json}' to describe their values, aesthetic, and approach to love. Reference Venus's core themes: '{venus_core_theme_json}'. Mention key Venus aspects, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Use JSON for Venus sign/house/theme and reference aspects list
            "2. **7th House (Descendant) - Your Partnership Mirror:** Describe the qualities sought or projected onto partners based on the 7th House. Use the provided interpretation for the sign on the cusp ({house_7_cusp_sign}): '{house_7_sign_interp_json}'. Use the provided interpretation for the house themes: '{house_7_core_themes_json}'. Discuss the influence of any planets located here ({house_7_planets_str}), referring to their provided planet in house interpretations from {all_planet_house_interps_json}.\n" # Use JSON for House 7 themes/cusp, and reference list for planets in house
            "3. **Relational Dynamics:** Briefly touch upon the interplay between attraction (Venus) and assertion (Mars) indicated by their aspects to each other, referring to the provided list of all aspect interpretations: {all_aspect_interps_json}.\n" # Reference aspects list
            "4. Synthesize these, offering insight into their path towards fulfilling connection. Finish with a reflective or mythic line about partnership."
        ),
        "word_count": 550,
        "meta": {
            "tone_mode": "reflective", # Changed from default based on Task 4 plan
            "tactics": ["Empathic Mirroring", "Attachment Archetypes"], # Changed based on Task 4 plan
            "theme": "Relational Mirror" # Changed from default based on Task 4 plan
        }
    },

    "15_Archetypes": {
        "header": "Archetypes",
        "quote": "“You are the myth made flesh.” — Carl Jung (paraphrased)",
        "static_intro": (
            "Sun, Moon, Rising, and pivotal conjunctions activate your personal pantheon of archetypes."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "Identify and briefly describe the core archetypes activated in {client_name}'s inner pantheon (approx 550 words):\n"
            "1. **The Core Self:** Archetype associated with the Sun in {sun_sign}. Use the provided interpretation: '{sun_sign_interp_json}'.\n" # Use JSON
            "2. **The Mask/Persona:** Archetype associated with the Ascendant/Rising sign {asc_sign}. Use the provided interpretation: '{asc_sign_interp_json}'.\n" # Use JSON
            "3. **The Inner Nurturer/Emotional Self:** Archetype associated with the Moon in {moon_sign}. Use the provided interpretation: '{moon_sign_interp_json}'.\n" # Use JSON
            "4. **Blended Archetypes:** Discuss any archetypal blending suggested by significant conjunctions involving personal planets. Refer to the provided list of major aspect interpretations: {major_aspect_interps_json}. Focus on the interpretations for conjunctions.\n" # Reference JSON list for conjunctions
            "5. Briefly discuss any insights from the provided list of Midpoint interpretations: {midpoint_interps_json}.\n" # Reference JSON list for midpoints
            "6. Briefly discuss any insights from the provided list of Aspect Pattern interpretations: {aspect_pattern_interps_json}.\n" # Reference JSON list for patterns
            "7. Weave these together, suggesting how these inner figures interact. Conclude with the closing question: “Which archetypal voice within you will you consciously amplify now?”"
        ),
        "word_count": 550,
        "meta": {
            "tone_mode": "reflective", # Changed from default based on Task 4 plan
            "tactics": ["Archetypal Reflection", "Inner Mirror Anchoring"], # Changed based on Task 4 plan
            "theme": "Sacred Self" # Changed from default based on Task 4 plan
        }
    },

    "16_Sensory_Signature": {
        "header": "Sensory Signature",
        "quote": "“Your fragrance is not of the Earth — it is the memory of where you came from.” — Mystic Sufi Aphorism",
        "static_intro": (
            "Ascendant, Venus, Moon, and elemental blend craft the aura others sense as scent, color, and vibration."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "Describe {client_name}’s unique 'Sensory Signature' (approx 500 words) – the subtle energetic and aesthetic aura they project:\n"
            "1. **The Aura/Presence:** How does the Ascendant in {asc_sign} shape the immediate energetic feel or 'color' they emanate? Use the provided interpretation: '{asc_sign_interp_json}'.\n" # Use JSON
            "2. **The Magnetic Field:** How does Venus in {venus_sign} influence their style, aesthetic preferences, and what they naturally attract or find beautiful? Use the provided interpretation: '{venus_sign_interp_json}'.\n" # Use JSON
            "3. **The Emotional Tone:** How does the Moon in {moon_sign} set the underlying emotional 'sound' or feeling tone they carry? Use the provided interpretation: '{moon_sign_interp_json}'.\n" # Use JSON
            "4. **The Elemental Essence:** How might their dominant element ({dominant_element}) translate into a sensory quality (e.g., Fire's heat/radiance, Earth's solidity/scent, Air's lightness/clarity, Water's fluidity/depth)? Use the provided interpretation: '{dom_elem_interp_json}'.\n" # Use JSON
            "Use rich sensory language (scent, color, texture, sound, feeling) throughout."
        ),
        "word_count": 500,
        "meta": {
            "tone_mode": "intro", # Changed from default based on Task 4 plan
            "tactics": ["Sensory Anchoring", "Narrative Transport"], # Changed from default based on Task 4 plan
            "theme": "Energetic Signature" # Changed from default based on Task 4 plan
        }
    },

    "17_Quantum_Timelines": {
        "header": "Quantum Timelines",
        "quote": "“Each transit is a fork in reality.” — Esoteric Astrology Codex",
        "static_intro": (
            "Transits open gateways into alternate futures—choose your path wisely."
        ),
        # <<< Prompt uses formatted string, needs minor adjustment to reference aspects list >>>
        "ai_prompt": (
            "Considering {client_name}'s age ({age}) and upcoming major transits ({future_transits_str}), outline three potential 'Quantum Timeline' scenarios for the next 12-18 months (approx 700 words).\n"
            "Refer to the provided list of interpretations for all aspects ({all_aspect_interps_json}). Use these interpretations to inform the themes, challenges, and opportunities presented by the key transits in each timeline scenario.\n\n" # Reference JSON list
            "1. For each scenario, identify 1-2 key transits from the {future_transits_str} list as major 'gateway' moments or decision points.\n"
            "2. Describe the potential theme, challenge, and opportunity presented by each timeline scenario in evocative, second-person language, drawing on the relevant aspect interpretations provided.\n"
            "3. Suggest one simple, symbolic **ritual or practice** to consciously engage with the energy of each theme.\n"
            "4. Conclude with a brief, empowering call to action, perhaps mentioning a related service like 'Astro Pulse' for ongoing guidance (frame this hypothetically if it's a real service).\n"
            "Frame this not as prediction, but as exploring potent fields of possibility accessible through conscious choice aligned with cosmic cycles."
        ),
        "word_count": 700,
        "meta": {
            "tone_mode": "technical", # Changed from default based on Task 4 plan
            "tactics": ["Future Visualization", "Narrative Transport"], # Changed from default based on Task 4 plan
            "theme": "Timeline Explorer" # Changed from default based on Task 4 plan
        }
    },

    "18_Quantum_Mirror": {
        "header": "Quantum Mirror",
        "quote": "“What if every person is a hologram of your own quantum field?” — The Living Codex",
        "static_intro": (
            "Venus, Mars, Pluto, and Saturn reflect your relational and karmic patterns."
        ),
        # <<< Updated prompt to use JSON context keys and reference aspects list >>>
        "ai_prompt": (
            "Analyze the 'Quantum Mirror' of relationships for {client_name} (approx 600 words). How might key relationships reflect inner dynamics?\n"
            "Refer to the provided interpretations for sign placements (Venus - '{venus_sign_interp_json}', Mars - '{mars_sign_interp_json}', Pluto - '{pluto_sign_interp_json}', Saturn - '{saturn_sign_interp_json}'). Also refer to the provided list of all aspect interpretations ({all_aspect_interps_json}).\n" # Reference JSON
            "1. **Attraction & Assertion:** Discuss the interplay between Venus in {venus_sign} and Mars in {mars_sign}. How might this dynamic manifest in partnership choices or conflicts? Synthesize the sign interpretations and relevant aspects.\n"
            "2. **Transformation & Structure:** Discuss the interplay between Pluto in {pluto_sign} and Saturn in {saturn_sign}. How might this axis influence deeper karmic lessons or power dynamics within relationships? Synthesize the sign interpretations and relevant aspects.\n"
            "3. Synthesize these, identifying a core repeating theme or pattern {client_name} might encounter in their relational mirroring."
        ),
        "word_count": 600,
        "meta": {
            "tone_mode": "reflective", # Changed from default based on Task 4 plan
            "tactics": ["Empathic Mirroring", "Shadow Integration"], # Changed from default based on Task 4 plan
            "theme": "Quantum Reflection" # Changed from default based on Task 4 plan
        }
    },

    "19_Transits_Forecasts": {
        "header": "Transits & Forecasts",
        "quote": "“Jupiter expands. Pluto transforms. The sky is your divine calendar.” — Celestial Almanac, 412 BCE",
        "static_intro": (
            "Upcoming transits forecast your spiritual weather—prepare for expansion, challenge, and transformation."
        ),
        # <<< Prompt uses formatted string, needs minor adjustment to reference aspects list >>>
        "ai_prompt": (
            "Provide an insightful forecast (approx 650 words) for {client_name} based on the upcoming transits: {future_transits_str}.\n"
            "Refer to the provided list of interpretations for all aspects ({all_aspect_interps_json}). Use these interpretations to inform the themes, challenges, and opportunities presented by the key transits in the forecast.\n\n" # Reference JSON list
            "1. Identify **three major themes** emerging from these transits for the next 12 months (e.g., 'Deepening Commitment', 'Career Transformation', 'Spiritual Awakening').\n"
            "2. For each theme, elaborate on the key transit(s) involved and the potential experiences, challenges, and growth opportunities, drawing on the relevant aspect interpretations provided.\n"
            "3. Suggest one simple, symbolic **ritual or practice** to consciously engage with the energy of each theme.\n"
            "4. Conclude with a brief, empowering call to action, perhaps mentioning a related service like 'Astro Pulse' for ongoing guidance (frame this hypothetically if it's a real service).\n"
            "Frame this not as prediction, but as exploring potent fields of possibility accessible through conscious choice aligned with cosmic cycles."
        ),
        "word_count": 650,
        "meta": {
            "tone_mode": "technical", # Changed from default based on Task 4 plan
            "tactics": ["Future Visualization", "Action Planning"], # Changed from default based on Task 4 plan
            "theme": "Celestial Navigator" # Changed from Task 4 plan
        }
    },

    "20_Spiritual_Awakening": {
        "header": "Spiritual Awakening",
        "quote": "“There is a light that shines beyond all things on Earth — this is the light within you.” — Chandogya Upanishad",
        "static_intro": (
            "Neptune, 12th House, and North Node chart your path of initiation and transcendence."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "Explore the path of Spiritual Awakening for {client_name} (approx 600 words) using these key 'coordinates':\n"
            "1. **Neptune's Invitation:** Analyze Neptune in {neptune_sign}. Expand on the provided interpretation '{neptune_sign_interp_json}' to discuss how it shapes their connection to the mystical, imaginative, or transcendent realms.\n" # Use JSON
            "2. **The 12th House Portal:** Describe the themes of the 12th House. Use the provided interpretation for the sign on the cusp ({house_12_cusp_sign}): '{house_12_sign_interp_json}'. Use the provided interpretation for the house themes: '{house_12_core_themes_json}'. Discuss the influence of any planets within ({house_12_planets_str}), referring to their provided planet in house interpretations from {all_planet_house_interps_json}.\n" # Use JSON for themes/cusp, reference list for planets
            "3. **North Node Direction:** Connect the spiritual path to their soul's purpose via the North Node ({north_node_sign} / House {north_node_house}). Weave in the essence of the provided interpretations: Sign - '{north_node_sign_interp_json}' and House - '{north_node_house_interp_json}'. Also consider the South Node sign ('{south_node_sign_interp_json}') and house ('{south_node_house_interp_json}').\n" # Use JSON
            "4. Synthesize these points, name one potential **spiritual mantra** resonant with their path, and offer a guiding insight about embracing their unique awakening journey."
        ),
        "word_count": 600,
        "meta": {
            "tone_mode": "ritual", # Changed from default based on Task 4 plan
            "tactics": ["Mystic Framing", "Soul Anchoring"], # Changed from default based on Task 4 plan
            "theme": "Awakened Seeker" # Changed from default based on Task 4 plan
        }
    },

    "21_Personalized_Guidance": {
        "header": "Personalized Guidance",
        "quote": "“The stars incline, they do not bind — it is your rhythm that makes the heavens dance.” — Alchemical Aphorism",
        "static_intro": (
            "Moon, Rising, Mercury, Venus, and Mars offer a toolbox of rituals, affirmations, and insights."
        ),
        # <<< Updated prompt to use JSON context keys >>>
        "ai_prompt": (
            "Provide personalized guidance (approx 500 words) for {client_name}, drawing insights from their placements. Generate practical, empowering suggestions:\n"
            "1. **Emotional Nourishment (Moon):** Based on their Moon in {moon_sign}. Use the provided interpretation: '{moon_sign_interp_json}'. Suggest two simple rituals or practices for emotional self-care and finding inner security.\n" # Use JSON
            "2. **Authentic Presence (Ascendant):** For their {asc_sign} Ascendant. Use the provided interpretation: '{asc_sign_interp_json}'. Offer two powerful affirmations to help them embody their authentic presence and navigate first impressions.\n" # Use JSON
            "3. **Mindful Communication (Mercury):** Considering Mercury in {mercury_sign}. Use the provided interpretation: '{mercury_sign_interp_json}'. Provide one key strategy for navigating communication challenges, especially during Mercury Retrograde periods.\n" # Use JSON
            "4. **Relational Harmony (Venus/Mars):** Based on Venus in {venus_sign} and Mars in {mars_sign}. Use the provided interpretations: Venus - '{venus_sign_interp_json}', Mars - '{mars_sign_interp_json}'. Offer one practical tip for enhancing harmony or navigating tension in relationships. Also refer to the provided list of all aspect interpretations ({all_aspect_interps_json}) for insights into their Venus-Mars dynamic.\n" # Use JSON and reference aspects list
            "5. **Soul Growth Path (Nodes):** Reflecting on their Nodal axis (NN {north_node_sign}/H{north_node_house}). Use the provided interpretations: North Node Sign - '{north_node_sign_interp_json}', North Node House - '{north_node_house_interp_json}', South Node Sign - '{south_node_sign_interp_json}', South Node House - '{south_node_house_interp_json}'. Pose one insightful journaling question to encourage exploration of their soul's evolutionary path.\n" # Use JSON
        ),
        "word_count": 500,
        "meta": {
            "tone_mode": "ritual", # Changed from default based on Task 4 plan
            "tactics": ["Action Planning", "Affirmation Anchoring"], # Changed from default based on Task 4 plan
            "theme": "Empowered Alchemist" # Changed from Task 4 plan
        }
    },

    "22_Final_Message": {
        "header": "Final Message",
        "quote": "“You are co-author of your myth.” — Cosmic Sage",
        "static_intro": (
            "You are not a passenger of your chart — you are its co-author. Walk forward as both character and creator in your own legend."
        ),
        # <<< Updated prompt to use JSON context keys and include previous closing logic >>>
        "ai_prompt": (
            "Craft a 300‑word closing blessing for {client_name} that:\n"
            "1. Briefly reflects the essence of their Sun ({sun_sign}, provided interpretation: {sun_sign_interp_json}), Ascendant ({asc_sign}, provided interpretation: {asc_sign_interp_json}), and Chart Ruler ({chart_ruler_planet}, provided interpretation: {chart_ruler_interp_json}).\n" # Use JSON
            "2. Reminds them that their birth chart is a dynamic map for a journey, not a fixed destiny – a cosmic dialogue they actively participate in.\n"
            "3. Ends with a short, powerful, uplifting affirmation tailored to their core signature (Sun/Asc/Ruler).\n\n"
            "-- Occasion Closing --\n\n" # Separator for the two parts of the prompt
            "Reflect the tone and purpose of this report. This is a {occasion_mode} astrology report.\n" # Include occasion context
            "If 'birthday': include themes of solar renewal, radiant becoming, and joyful affirmation.\n"
            "If 'rebirth': speak of cycles, sacred flame, inner rising.\n"
            "If 'career': reference purpose, contribution, inner compass.\n"
            "If 'self_discovery': use soul mirror metaphors, insight, identity integration.\n"
            "If 'relationship': reflect themes of love, inner wholeness, mirrored lessons.\n"
            "If 'dark_night': use tone of gentle hope, resilience, and light in shadows.\n\n"
            "Close with a poetic blessing or invocation."
        ),
        "word_count": 300,
        "meta": {
            "tone_mode": "reflective", # Changed from default based on Task 4 plan
            "tactics": ["Emotional Closure", "Narrative Transport"], # Changed from default based on Task 4 plan
            "theme": "Co-Creator" # Changed from default based on Task 4 plan
        }
    }
}