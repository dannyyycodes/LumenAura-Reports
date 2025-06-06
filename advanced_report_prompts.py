# START OF FILE advanced_report_prompts.py

import logging
import html
import re
import copy # Import copy for deepcopy
from collections import defaultdict # Keep if needed by _insert_symbols maybe?

# --- Version ---
# Represents the structure of this loader script
__version__ = "38.0.0" # New Version

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - PROMPTS - %(message)s')

1.theres still '(Mika’s Voice:' throughout this shouldnt be displayed . 2. the planet and sign sybols arent working any more they are just showing as black boxes .

# --- Helper: Symbol Insertion (Using the robust version) ---
# This function adds symbols to STATIC text before it goes to the PDF generator.
def _insert_symbols(text):
    """Inserts astrological symbols into text using DejaVuSans font tags."""
    if not isinstance(text, str): return text
    processed_text = text
    # Sort by length to match longer names first (e.g., "North Node" before "Node")
    sorted_symbols = sorted(SYMBOLS.items(), key=lambda item: len(item[0]), reverse=True)

    for term, symbol in sorted_symbols:
        # Use word boundaries to avoid partial matches, case-insensitive
        pattern = r'\b' + re.escape(term) + r'\b'
        escaped_symbol = html.escape(symbol)
        # Format for ReportLab paragraph (assumes DejaVuSans font is registered in PDF generator)
        replacement = f"{term} <font name='DejaVuSans'>{escaped_symbol}</font>"

        # Context-aware replacement to avoid replacing inside HTML tags or attributes
        def context_aware_replace(match):
            # Basic check: don't replace if adjacent chars suggest it's inside a tag/attribute
            start_index = match.start()
            end_index = match.end()
            preceding_char = match.string[start_index - 1] if start_index > 0 else ' '
            following_char = match.string[end_index] if end_index < len(match.string) else ' '
            # Add more checks if needed (e.g., checking if inside quotes)
            if preceding_char in ('"', "'", '/', '=', '-', '<', '>') or \
               following_char in ('"', "'", '=', '-', '<', '>'):
                return match.group(0) # Return original match
            else:
                return replacement # Perform replacement

        try:
             # Apply the replacement using the context-aware function
             processed_text = re.sub(pattern, context_aware_replace, processed_text, flags=re.IGNORECASE)
        except Exception as sub_err:
             logger.error(f"Error during re.sub for term '{term}': {sub_err}")
             # Continue processing other terms even if one fails

    # Optional basic cleanup for common issues with ReportLab tags
    processed_text = processed_text.replace("<b> ", "<b>").replace(" </b>", "</b>")
    processed_text = processed_text.replace("<i> ", "<i>").replace(" </i>", "</i>")
    processed_text = processed_text.replace("<font ", "<font").replace(" </font>", "</font>")
    processed_text = processed_text.replace(" >", ">")

    return processed_text

# --- Main Function to Get Prompts (Refactored) ---
def get_advanced_report_prompts(birth_chart, client_name="", gender="Prefer not to say", future_transits=None):
    """
    Loads the finalized PROMPTS dictionary from prompt_definitions.py
    and optionally processes static text parts (like inserting symbols).
    """
    logger.info(f"Loading prompt definitions (V{__version__})...")

    try:
        # Import the finalized prompts from the dedicated file
        # This requires prompt_definitions.py to be in the Python path
        from prompt_definitions import PROMPTS
        if not isinstance(PROMPTS, dict):
             raise ImportError("PROMPTS dictionary not found or invalid in prompt_definitions.py")
        logger.info(f"Loaded {len(PROMPTS)} section definitions from prompt_definitions.py.")

        # Create a deep copy to avoid modifying the original imported dict
        processed_prompts = copy.deepcopy(PROMPTS)

        # --- Optional: Insert symbols into STATIC text parts ---
        # This modifies the dictionary that will be returned to the orchestrator
        logger.info("Processing symbols for static text parts...")
        sections_processed_count = 0
        for key, section_data in processed_prompts.items():
             if isinstance(section_data, dict):
                 try:
                     if 'static_intro' in section_data:
                         section_data['static_intro'] = _insert_symbols(section_data.get('static_intro', ''))
                     if 'static_outro' in section_data: # If you add outros later
                         section_data['static_outro'] = _insert_symbols(section_data.get('static_outro', ''))
                     # Add any other static fields that might need symbol processing here
                     sections_processed_count += 1
                 except Exception as symbol_err:
                     logger.error(f"Error inserting symbols for section '{key}': {symbol_err}", exc_info=False)
                     # Add error flag or note to the section data?
                     section_data['error_flag_symbol'] = True
                     section_data['static_intro'] = section_data.get('static_intro', '') + f"\n[Symbol Insertion Error]"

        logger.info(f"Symbol processing completed for {sections_processed_count} sections.")
        return processed_prompts

    except ImportError as e:
         logger.critical(f"Could not import PROMPTS from prompt_definitions.py: {e}")
         return {"error": f"Failed to load prompt definitions: {e}"}
    except Exception as e:
        error_msg = f"Unexpected error loading/processing prompts: {e}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}

# --- Example Usage Block (Updated for new structure) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - PROMPTS-TEST - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', force=True)
    logger.setLevel(logging.DEBUG)
    logger.info(f"--- Testing advanced_report_prompts.py Structure (V{__version__}) ---")

    # Create a dummy prompt_definitions.py for testing if it doesn't exist
    import os
    if not os.path.exists("prompt_definitions.py"):
         logger.warning("prompt_definitions.py not found, creating dummy version for test.")
         with open("prompt_definitions.py", "w") as f:
             f.write("PROMPTS = {\n")
             # Add a couple of dummy sections matching the expected structure
             f.write("    '00_Cover_Page': {'header': '', 'quote': '', 'static_intro': '', 'ai_prompt': '', 'word_count': 0, 'meta': {'skip_ai': True}},\n")
             f.write("    '01_Mythic_Prologue': {\n")
             f.write("        'header': 'Mythic Prologue',\n")
             f.write("        'quote': 'Test Quote with Sun',\n") # Test symbol insertion
             f.write("        'static_intro': 'Welcome Test Client. Your Sun is a star. Your Moon reflects.',\n") # Test symbols
             f.write("        'ai_prompt': 'Hello {client_name}, your Sun is {sun_sign}.',\n")
             f.write("        'word_count': 10,\n")
             f.write("        'meta': {},\n")
             f.write("    },\n")
             f.write("    '02_Client_Details': {'header': 'Client Details', 'quote': '', 'static_intro': 'Data for Ascendant.', 'ai_prompt': '', 'word_count': 0, 'meta': {'skip_ai': True}}\n") # Test skip_ai and symbol
             f.write("}\n")
         logger.info("Created dummy prompt_definitions.py.")

    # Mock input data (less critical now, only needed if function used them)
    mock_chart = {"birth_details": {}}
    mock_transits = {}

    # Call the refactored function
    prompts_result = get_advanced_report_prompts(mock_chart, "Test Client", "They/Them", mock_transits)

    if isinstance(prompts_result, dict) and "error" not in prompts_result:
        logger.info(f"Successfully loaded and processed {len(prompts_result)} prompt structures.")
        # Check a sample section
        sample_key = '01_Mythic_Prologue'
        if sample_key in prompts_result:
            logger.info(f"--- Sample Section '{sample_key}' ---")
            logger.info(f"Header: {prompts_result[sample_key].get('header')}")
            logger.info(f"Static Intro (Processed): {prompts_result[sample_key].get('static_intro')}")
            logger.info(f"AI Prompt Template: {prompts_result[sample_key].get('ai_prompt')}")
            logger.info(f"Word Count: {prompts_result[sample_key].get('word_count')}")
            logger.info(f"Meta: {prompts_result[sample_key].get('meta')}")
            # Check if symbols were inserted
            if "<font name='DejaVuSans'>" in prompts_result[sample_key].get('static_intro',''):
                logger.info("    ✅ Symbols appear inserted in static intro.")
            else:
                 logger.warning("    ⚠️ Symbols may be missing from static intro.")
        else:
            logger.warning(f"Sample key '{sample_key}' not found in result.")

        sample_key_2 = '02_Client_Details'
        if sample_key_2 in prompts_result:
             logger.info(f"--- Sample Section '{sample_key_2}' ---")
             logger.info(f"Meta: {prompts_result[sample_key_2].get('meta')}")
             if prompts_result[sample_key_2].get('meta', {}).get('skip_ai'):
                  logger.info("    ✅ skip_ai flag is correctly set to True.")
             else:
                  logger.error("    ❌ skip_ai flag is NOT set correctly for Section 02.")
             if "<font name='DejaVuSans'>" in prompts_result[sample_key_2].get('static_intro',''):
                logger.info("    ✅ Symbols appear inserted in static intro for Sec 02.")

    else:
        logger.error(f"Test failed: {prompts_result}")

    logger.info("--- Prompt Loading / Static Processing Test Complete ---")


# --- END OF FILE advanced_report_prompts.py ---