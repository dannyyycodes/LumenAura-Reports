# voice_engine.py
# VERSION 1.1.4 - PATCH 12: Refined Pronoun System & Memorial Voice
# VERSION 1.1.2 - PATCH 11: Memorial Mode Cleanup & Visual Fixes (Avoid they/their)
# VERSION 1.1.1 - PATCH 10: Memorial Mode Finalization (Tone & Tense)
# VERSION 1.1.0 - Interjection control, tone softening, memorial mode
# Applies persona tone, psychological tactics, and narrative overlays to astrology prompts
# Includes logic for pet reports and basic SSML for TTS guidance

import re # Needed for potential future SSML parsing if needed, or just for good practice
import logging

logger = logging.getLogger(__name__)

# --- Pet Report Configuration ---
PET_VOICE_PERSONA = "Mika"
# Define pet-specific tactics and tone mode
PET_TACTICS = ["Humor Anchoring", "Pet Imagery", "Relatable Quirk Framing"]
PET_TONE_MODE = "playful"
# Species-specific interjections for the start of the prompt content
PET_SSML_INTERJECTIONS = {
    "dog": "<say-as interpret-as='interjection'>woof!</say-as>",
    "cat": "<say-as interpret-as='interjection'>meow.</say-as>",
    "bird": "<say-as interpret-as='interjection'>chirp!</say-as>",
    "hamster": "<say-as interpret-as='interjection'>squeak!</say-as>",
    "reptile": "<say-as interpret-as='interjection'>hiss.</say-as>", # A playful hiss!
    # Add others as needed
}
# Default interjection if species is not found in the mapping
PET_SSML_DEFAULT_INTERJECTION = "<say-as interpret-as='interjection'>grrr.</say-as>" # Using a generic friendly sound as default

# Sections where interjections are used in "auto" mode
INTERJECTION_INTRO_SECTIONS = ["toc", "sun_sign", "rising_sign"]


def apply_voice_to_prompt(
    base_prompt,
    persona="Elowen",
    tactics=None,
    directive=None,
    theme=None,
    client_name="",
    tone_mode="default",
    include_journal_prompt=False,
    clarity_first=True,
    species=None,
    section_id: str = None, # New parameter for interjection control
    interjection_mode: str = "auto", # New parameter: auto, always, never
    occasion_mode: str = None, # New parameter for memorial mode
    pronoun_mode: str = "name" # Refined PATCH 12: Changed from pet_gender, default "name"
):
    """
    Enriches a raw AI prompt with persona voice, psychology tactics, and spiritual narrative cues.
    Includes specific handling for pet reports and adds basic SSML wrapping for TTS guidance.

    :param base_prompt: Original prompt string from prompt_definitions.py
    :param persona: Name of the voice persona (e.g., 'Elowen' or 'Mika')
    :param tactics: List of psychological tactics/writing styles to weave into the tone
    :param directive: Optional mystical instruction to embed (e.g., 'Speak as if decoding a soul scroll')
    :param theme: Archetype or mythic motif to frame the response
    :param client_name: The name of the report recipient (human or pet), for personal tone
    :param tone_mode: intro / technical / karmic / ritual / default / playful — determines how poetic or grounded Elowen is, or sets pet playfulness
    :param include_journal_prompt: Whether to inject a final reflective journal prompt (disabled for pets)
    :param clarity_first: Ensures language is emotionally intuitive and avoids overly abstract metaphors (primarily for Elowen)
    :param species: Pet species (e.g., 'Dog', 'Cat').
    :param section_id: ID of the current report section (e.g., 'sun_sign', 'moon_sign'). Used for 'auto' interjection_mode.
    :param interjection_mode: Controls when pet interjections are used ("auto", "always", "never").
    :param occasion_mode: Special occasion for the report, e.g., "pet_memorial".
    :param pronoun_mode: Pronoun handling mode ("he", "she", "name") for memorial AI guidance.
    :return: Enhanced prompt string for GPT generation, including SSML wrapping.
    """
    # Use default mutable arguments safely
    if tactics is None:
        tactics = []

    # --- Detect Pet Reports & Apply Overrides ---
    is_pet_report = (persona.lower() == PET_VOICE_PERSONA.lower()) # Case-insensitive check

    if is_pet_report:
        logger.debug("Applying pet report voice overrides (Mika persona).")
        persona_to_use = PET_VOICE_PERSONA
        tactics_to_use = list(PET_TACTICS) # Use a copy to avoid modifying the constant
        tone_mode_to_use = PET_TONE_MODE
        include_journal_prompt_to_use = False # Disable journal prompts for pets
        clarity_first_to_use = True # Assume clarity is always desired for pets

        base_prompt_content = base_prompt.strip() # Default: no interjection initially

        # --- Species Interjection Control ---
        should_add_interjection = False
        # Interjections are usually not appropriate for memorial reports, so we skip if in memorial mode
        if occasion_mode != "pet_memorial":
            if interjection_mode == "always":
                should_add_interjection = True
            elif interjection_mode == "auto":
                if section_id and section_id.lower() in INTERJECTION_INTRO_SECTIONS:
                    should_add_interjection = True
            # If interjection_mode == "never", should_add_interjection remains False

        if should_add_interjection:
            interjection_tag = PET_SSML_DEFAULT_INTERJECTION # Start with default
            if species and isinstance(species, str):
                interjection_tag = PET_SSML_INTERJECTIONS.get(species.lower(), PET_SSML_DEFAULT_INTERJECTION)
                logger.debug(f"Selected pet interjection '{interjection_tag}' for species '{species}'.")
            else:
                logger.warning(f"Species not provided or invalid ('{species}'). Using default pet interjection.")
            base_prompt_content = f"{interjection_tag} {base_prompt_content}" # Prepend interjection
        # --- End Interjection Control ---

        directive_to_use = directive
        theme_to_use = theme

    else: # Human report (Elowen persona)
        logger.debug("Applying human report voice settings (Elowen persona).")
        persona_to_use = persona
        tactics_to_use = list(tactics)
        tone_mode_to_use = tone_mode
        include_journal_prompt_to_use = include_journal_prompt
        clarity_first_to_use = clarity_first
        base_prompt_content = base_prompt.strip()
        directive_to_use = directive
        theme_to_use = theme


    # --- Build AI Instruction Block ---
    ai_instruction_block = ""

    if persona_to_use == "Elowen":
        ai_instruction_block += (
            f"You are Elowen, a poetic oracle blending astrology, archetypal psychology, and celestial memory.\n"
            f"You speak to {client_name} in second-person ('you') as if guiding them through a soul scroll or sacred text.\n"
            "Your style is inspired by Rumi, Jung, and modern poetic mystics.\n"
        )
        if clarity_first_to_use:
            ai_instruction_block += (
                "Keep language clear, grounded, and emotionally intuitive, avoiding overly abstract metaphors.\n"
            )
        if tone_mode_to_use == "intro":
            ai_instruction_block += "Use rich metaphor and mythic time to open a portal into the section.\n"
        elif tone_mode_to_use == "technical":
            ai_instruction_block += "Be grounded, gently poetic, but clear and structured. Use metaphor sparingly.\n"
        elif tone_mode_to_use == "karmic":
            ai_instruction_block += "Speak with mystic reverence, as if translating soul contracts from the stars.\n"
        elif tone_mode_to_use == "ritual":
            ai_instruction_block += "Offer soft guidance. Encourage small rituals, mantras, or nature connection.\n"
        else:
            ai_instruction_block += "Maintain a balanced tone — poetic on edges, grounded at the center.\n"

    elif persona_to_use == PET_VOICE_PERSONA: # Mika persona (Pet Reports)
         ai_instruction_block += (
             f"You are {PET_VOICE_PERSONA}, a whimsical, heartful guide speaking about {client_name} (a pet) to their human guardian.\n"
             f"You speak about the pet’s unique traits to their human, in a loving and warm tone, without formal salutations.\n"
             f"Use clear metaphors and simple, warm language to explain astrology from a pet's perspective.\n"
         )
         # Mika Tone Modulation (Pet Playfulness / Memorial)
         # Refined PATCH 12: Updated Memorial Mode Instruction with pronoun_mode
         if occasion_mode == "pet_memorial":
            # Generate pronoun guidance based on pronoun_mode
            if pronoun_mode == "he":
                pronoun_rule = f"Refer to {client_name} as 'he' or 'him'. Avoid using 'they' or 'their'."
            elif pronoun_mode == "she":
                pronoun_rule = f"Refer to {client_name} as 'she' or 'her'. Avoid using 'they' or 'their'."
            else: # "name" or any other fallback
                pronoun_rule = f"Avoid using 'they' or 'their'. Refer to {client_name} by name throughout the report."

            ai_instruction_block += (
                f"\nIMPORTANT MEMORIAL CONTEXT: This report is a tribute to {client_name}, who has passed away. "
                f"Use past tense consistently. Frame your tone as a gentle memorial. {pronoun_rule}\n"
            )
         elif tone_mode_to_use == PET_TONE_MODE: # Playful (and not memorial)
              ai_instruction_block += f"Maintain a consistently {PET_TONE_MODE}, tongue-in-cheek, and humorous tone throughout, using relatable pet examples.\n"
         else: # Fallback pet tone (and not memorial)
              ai_instruction_block += "Maintain a generally warm and affectionate tone for a pet report.\n"

    if directive_to_use:
        ai_instruction_block += f"Oracle Directive: {directive_to_use}\n"

    if theme_to_use:
        ai_instruction_block += f"Frame your language as if describing the path of the '{theme_to_use}' archetype.\n"

    ai_instruction_block += "\n"

    if tactics_to_use:
        ai_instruction_block += "Writing Style / Techniques:\n"
        for tactic in tactics_to_use:
            ai_instruction_block += f"- {tactic}\n"
        ai_instruction_block += "\n"


    ssml_wrapped_content = f"<voice name='{persona_to_use}'><prosody rate='medium'>{base_prompt_content}</prosody></voice>"

    final_prompt_string = f"{ai_instruction_block.strip()}\n\nContent to Generate (within SSML tags below):\n{ssml_wrapped_content}"

    if include_journal_prompt_to_use:
         final_prompt_string += ("\n\nJournal Invitation: \n"
                                  "Close the section with a gentle journal invitation, such as: \n"
                                  "'Journal prompt: What emotions or memories rise when you reflect on this part of your chart?'")


    logger.debug(f"Generated prompt (start): {final_prompt_string[:500]}...")

    return final_prompt_string.strip()


# === Example Usage ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Enable debug logging for example

    # Example Human Report Prompt
    test_prompt_human = "In 250 words, describe {client_name}'s core essence using the chart ruler, unaspected planets, Sun/Ascendant dynamic, and dominant modality."
    tactics_human = ["Anchoring", "Archetypal Dialogue", "Mythic Time Collapse"]
    final_human = apply_voice_to_prompt(
        base_prompt=test_prompt_human,
        persona="Elowen",
        tactics=tactics_human,
        directive="Speak as if decoding a soul scroll",
        theme="Soul Rememberer",
        client_name="Aurora",
        tone_mode="intro",
        include_journal_prompt=True,
        clarity_first=True
    )
    print("--- Human Report Prompt Example ---")
    print(final_human)
    print("-" * 30)


    # Example Pet Report Prompt (Dog) - Auto Interjection Mode
    print("\n--- Pet Report Prompt Examples (Mika Persona) ---")
    test_prompt_pet_sun = "Describe {pet_name}'s Sun sign personality traits with playful examples of how these show up in dog or cat behavior."

    print("\nDog Sun Sign (auto interjection - should have 'woof'):")
    final_pet_dog_sun = apply_voice_to_prompt(
        base_prompt=test_prompt_pet_sun,
        persona=PET_VOICE_PERSONA,
        client_name="Buster",
        species="Dog",
        section_id="sun_sign", # Intro section
        interjection_mode="auto"
    )
    print(final_pet_dog_sun)

    print("\nDog Moon Sign (auto interjection - should NOT have 'woof'):")
    test_prompt_pet_moon = "Describe {pet_name}'s Moon sign emotional style."
    final_pet_dog_moon = apply_voice_to_prompt(
        base_prompt=test_prompt_pet_moon,
        persona=PET_VOICE_PERSONA,
        client_name="Buster",
        species="Dog",
        section_id="moon_sign", # Not an intro section
        interjection_mode="auto"
    )
    print(final_pet_dog_moon)

    print("\nCat Sun Sign (always interjection - should have 'meow'):")
    final_pet_cat_sun_always = apply_voice_to_prompt(
        base_prompt=test_prompt_pet_sun,
        persona=PET_VOICE_PERSONA,
        client_name="Whiskers",
        species="Cat",
        section_id="sun_sign",
        interjection_mode="always"
    )
    print(final_pet_cat_sun_always)

    print("\nBird Rising Sign (never interjection - should NOT have 'chirp'):")
    test_prompt_pet_rising = "Highlight {pet_name}’s rising sign energy."
    final_pet_bird_rising_never = apply_voice_to_prompt(
        base_prompt=test_prompt_pet_rising,
        persona=PET_VOICE_PERSONA,
        client_name="Pip",
        species="Bird",
        section_id="rising_sign",
        interjection_mode="never"
    )
    print(final_pet_bird_rising_never)

    print("\nDog Sun Sign (Memorial Mode - MALE pronoun_mode='he'):")
    final_pet_dog_sun_memorial_he = apply_voice_to_prompt(
        base_prompt=test_prompt_pet_sun,
        persona=PET_VOICE_PERSONA,
        client_name="Buddy",
        species="Dog",
        section_id="sun_sign",
        interjection_mode="never",
        occasion_mode="pet_memorial",
        pronoun_mode="he"
    )
    print(final_pet_dog_sun_memorial_he)

    print("\nCat Moon Sign (Memorial Mode - FEMALE pronoun_mode='she'):")
    final_pet_cat_moon_memorial_she = apply_voice_to_prompt(
        base_prompt=test_prompt_pet_moon,
        persona=PET_VOICE_PERSONA,
        client_name="Luna",
        species="Cat",
        section_id="moon_sign",
        interjection_mode="never",
        occasion_mode="pet_memorial",
        pronoun_mode="she"
    )
    print(final_pet_cat_moon_memorial_she)

    print("\nReptile Moon Sign (Memorial Mode - NAME pronoun_mode='name'):")
    final_pet_reptile_moon_memorial_name = apply_voice_to_prompt(
        base_prompt=test_prompt_pet_moon,
        persona=PET_VOICE_PERSONA,
        client_name="Slinky",
        species="Reptile",
        section_id="moon_sign",
        interjection_mode="never",
        occasion_mode="pet_memorial",
        pronoun_mode="name" # or not provided, defaults to "name"
    )
    print(final_pet_reptile_moon_memorial_name)

    print("-" * 30)
#--- END OF FILE voice_engine.py ---