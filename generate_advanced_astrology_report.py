# generate_advanced_astrology_report.py
# --- VERSION 22.56.8 — Removed pdf_generator_version_marker import ---
# --- VERSION 22.56.7 — Apply import and path fixes for package structure ---
# --- VERSION 22.56.5 — Fix TypeError with species/breed in calculate_chart call ---
# (Previous history...)

import os
import re # Ensure re is imported for validator
import json # Ensure json is imported
import traceback
# import requests # <<< REMOVED
from datetime import datetime, timezone, timedelta, date # Added date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # <<< ADDED for consistency
from io import BytesIO # Keep if used elsewhere or for future additions (e.g., image handling)
import tempfile
# import pytz # <<< REMOVED
import logging # Ensure logging is imported for validator
from collections import defaultdict, Counter # Added Counter
import copy
import argparse
import math # Ensure math is imported
from itertools import combinations # Needed for pattern detection
from dateutil.relativedelta import relativedelta # Needed for future transits

# --- Define Version ---
# <<< VERSION UPDATED >>>
__version__ = "22.56.8" # Version reflects marker removal

# --- OpenAI Client Setup ---
# Attempt to import specific errors for better handling
try:
    from openai import OpenAI, OpenAIError, AuthenticationError
except ImportError:
    # Define dummy exceptions if openai library is not installed
    class OpenAIError(Exception): pass
    class AuthenticationError(Exception): pass
    logging.warning("OpenAI library not found. AI functionality will be disabled (TEST_MODE forced).") # Use logger

client = None
TEST_MODE = True # Default to False # <<< REMAINS TRUE AS PER USER REQUEST

try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        TEST_MODE = True # Force Test Mode if no API key
        print("WARNING: OPENAI_API_KEY environment variable not set. Forcing TEST MODE. AI calls will be mocked.")
    else:
        client = OpenAI(api_key=openai_api_key)
        # Optional: Add a simple check here if needed, e.g., listing models (can consume tokens)
        # try:
        #     client.models.list()
        #     print("OpenAI client initialized and authenticated.")
        # except AuthenticationError:
        #     print("WARNING: OpenAI Authentication Error with provided key. Forcing TEST MODE.")
        #     TEST_MODE = True
        #     client = None
        # except Exception as api_check_err:
        #     print(f"Warning: Could not verify OpenAI client connection: {api_check_err}. Proceeding.")
        # If initialization doesn't raise an error, assume okay for now.
        if not TEST_MODE: # Only print if not already forced into test mode
            print("OpenAI client initialized.")

except NameError: # Handle case where OpenAI class itself wasn't imported
    TEST_MODE = True
    print("WARNING: OpenAI library not found or failed to import. Forcing TEST MODE.")
except AuthenticationError as auth_err:
    TEST_MODE = True
    print(f"WARNING: OpenAI Authentication Error: {auth_err}. Forcing TEST MODE.")
    client = None # Ensure client is None on auth error
except Exception as client_err:
    TEST_MODE = True # Force Test Mode on other init errors
    print(f"WARNING: Error initializing OpenAI client: {client_err}. Forcing TEST MODE.")
    client = None # Ensure client is None

# --- Configure Logger ---
logger = logging.getLogger(__name__)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
if log_level not in valid_log_levels:
    print(f"Warning: Invalid LOG_LEVEL '{log_level}'. Defaulting to INFO.")
    log_level = "INFO"
numeric_level = getattr(logging, log_level, logging.INFO)

if not logger.handlers:
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(numeric_level)
    logger.info(f"Logger '{__name__}' configured with level {log_level}.")
else:
    # Ensure level is updated if logger already exists
    logger.setLevel(numeric_level)
    # Avoid adding handlers again if already configured (e.g., in interactive sessions)
    logger.info(f"Logger '{__name__}' already configured. Level set to {log_level}.")


# --- Import Local Modules (Corrected for Package Structure) ---
try:
    # Absolute import from the common package:
    from common.json_loader import load_json_data, DATA_JSON_DIR as COMMON_DATA_JSON_DIR
    logger.info("load_json_data and COMMON_DATA_JSON_DIR imported from common.json_loader.")
    JSON_LOADER_AVAILABLE = True
except ImportError as e:
    logger.critical(f"FATAL ERROR importing from 'common.json_loader': {e}. JSON loading will fail.")
    JSON_LOADER_AVAILABLE = False
    # Define fallbacks if json_loader is critical
    def load_json_data(group): return None
    COMMON_DATA_JSON_DIR = None # This will cause issues if not handled downstream

try:
    # Relative import for HUMAN_PROMPTS from sibling file in human_report package:
    from .prompt_definitions import HUMAN_PROMPTS
    logger.info("HUMAN_PROMPTS imported from .prompt_definitions.")
except ImportError as e:
    # Check if the error is specifically 'cannot import name HUMAN_PROMPTS'
    if "cannot import name 'HUMAN_PROMPTS'" in str(e):
         logger.critical(f"FATAL ERROR: Variable 'HUMAN_PROMPTS' not found in human_report/prompt_definitions.py. Please check spelling/definition.")
    else:
         logger.critical(f"FATAL ERROR: Cannot import from .prompt_definitions: {e}")
    HUMAN_PROMPTS = {} # Use empty dict as fallback


# --- Load Occasion Styles Configuration ---
# This now uses load_json_data from common.json_loader, which looks in common/Data jsons/
OCCASION_STYLES_FROM_ORCHESTRATOR = {}
if JSON_LOADER_AVAILABLE:
    logger.info(f"Orchestrator attempting to load occasion styles using common.json_loader (expected in common/Data jsons/)...")
    OCCASION_STYLES_FROM_ORCHESTRATOR = load_json_data('occasion_styles') # load_json_data looks for 'occasion_styles.json'
    if OCCASION_STYLES_FROM_ORCHESTRATOR:
        logger.info(f"Orchestrator successfully loaded occasion styles ({len(OCCASION_STYLES_FROM_ORCHESTRATOR)} modes).")
    else:
        logger.warning(f"Orchestrator: Could not load 'occasion_styles.json' via common.json_loader. Occasion-specific overrides may be missing or file is empty/corrupt in common/Data jsons/.")
        OCCASION_STYLES_FROM_ORCHESTRATOR = {} # Ensure it's a dict
else:
    logger.error("Orchestrator: common.json_loader not available. Cannot load occasion styles.")
    OCCASION_STYLES_FROM_ORCHESTRATOR = {}


# Continue importing other modules (many are now common)
try:
    # Adjusted for package structure (assuming prompt_definitions_pet.py is in pet_report/)
    from pet_report.prompt_definitions_pet import PROMPTS as PET_PROMPTS
    logger.info("PET_PROMPTS imported from pet_report.prompt_definitions_pet.")
except ImportError:
    logger.warning("WARNING: Cannot import PET_PROMPTS from pet_report.prompt_definitions_pet.")
    PET_PROMPTS = {} # Fallback to empty dict

# get_interpretation is also in common.json_loader, already handled by the import above
# For simplicity, if you were using get_interpretation directly here, you'd call common.json_loader.get_interpretation

try:
    # Assuming pet_blessings_by_occasion.py would be in pet_report/
    from pet_report.pet_blessings_by_occasion import PET_BLESSINGS
    logger.info("PET_BLESSINGS imported.")
except ImportError:
    logger.warning("WARNING: Cannot import PET_BLESSINGS. Pet blessings will not be appended.")
    PET_BLESSINGS = {}

try:
    # Adjusted for package structure (assuming voice_engine.py is in common/)
    from common.voice_engine import apply_voice_to_prompt
    logger.info("apply_voice_to_prompt imported from common.voice_engine.")
except ImportError as e:
    logger.critical(f"FATAL ERROR importing apply_voice_to_prompt from 'common.voice_engine': {e}"); raise

try:
    # Adjusted for package structure (assuming advanced_calculate_astrology.py is in common/)
    from common.advanced_calculate_astrology import calculate_chart, get_zodiac_sign, swe, __version__ as calc_version
    logger.info(f"Calculation engine imported (V{calc_version}). Swisseph object potentially imported.")
except ImportError as e:
    logger.critical(f"FATAL ERROR importing from common.advanced_calculate_astrology: {e}"); raise
except AttributeError:
    logger.warning("Swe obj not found in common.advanced_calculate_astrology, ensure it's handled there if needed globally.")
    swe = None

try:
    # Assuming advanced_report_prompts.py would also be in common if it's general utility
    # If it's specific to human_report, it would be from .advanced_report_prompts
    # Since it defines _insert_symbols, let's assume it's in common.
    from common.advanced_report_prompts import _insert_symbols, SYMBOLS
    logger.info("Imported _insert_symbols and SYMBOLS from common.advanced_report_prompts.")
except ImportError as e:
    logger.warning(f"Could not import helpers from common.advanced_report_prompts: {e}")
    def _insert_symbols(text): return text
    SYMBOLS = {}

try:
    # Import the HUMAN PDF generator function from human_report.py within the same package
    # <<< FIXED IMPORT LINE >>>
    from .human_report import generate_human_pdf
    # Assuming generate_human_pdf doesn't expose a version marker, or we don't need it here.
    logger.info(f"Human PDF generator imported from .human_report.")
except ImportError as e:
    logger.critical(f"FATAL ERROR importing generate_human_pdf from .human_report: {e}")
    # Define dummy if critical for script to run further for testing other parts
    def generate_human_pdf(**kwargs): logger.error("Dummy generate_human_pdf called due to import error."); return False
    # pdf_generator_version_marker = "N/A" # Variable removed


# --- Optional Imports ---
try: import cairosvg; _cairosvg_available = True; logger.info("CairoSVG found.")
except ImportError: _cairosvg_available = False; logger.warning("CairoSVG not found (PNG chart generation skipped).")
try: from kerykeion import AstrologicalSubject, KerykeionChartSVG; _kerykeion_available = True; KerykeionClass = AstrologicalSubject; ChartMakerClass = KerykeionChartSVG; logger.info("Kerykeion imported.")
except ImportError as e: _kerykeion_available = False; KerykeionClass = None; ChartMakerClass = None; logger.warning(f"Kerykeion import failed: {e}...")

try:
    # Assuming section_layout_presets.py would be in common if used by both
    # Path needs clarification based on where this file lives. Using fallback for now.
    # from common.section_layout_presets import SECTION_LAYOUT_PRESETS
    logger.warning("section_layout_presets.py import path needs clarification. Using fallback.")
    SECTION_LAYOUT_PRESETS = {}
except ImportError:
    logger.warning("WARNING: Cannot import SECTION_LAYOUT_PRESETS. Using empty dict.")
    SECTION_LAYOUT_PRESETS = {}


# --- Configuration ---
# Ephemeris Path Setup (robust check)
DEFAULT_EPHE_PATH = "/path/to/your/ephemeris/files" # Needs to be set correctly
# DEFAULT_EPHE_PATH = r"C:\path\to\your\ephemeris\files"; # Windows Example
ephe_path = None
try:
    # Get directory containing *this* script (human_report/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()
    logger.debug("Using current working directory for relative path calculation.")

# Define project root relative to this script (human_report/)
project_root_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

possible_paths = [
    os.getenv('SWEPHE_PATH'),
    DEFAULT_EPHE_PATH,
    os.path.join(project_root_dir, 'swisseph'), # Check for 'swisseph' at project root
    os.path.join(project_root_dir, 'ephe')      # Check for 'ephe' at project root
]
for p in possible_paths:
    if p and os.path.isdir(p):
        ephe_path = os.path.abspath(p)
        logger.info(f"Using ephemeris path: {ephe_path}")
        break

if not ephe_path:
    logger.critical("Ephemeris path not found in SWEPHE_PATH, default path, or relative 'ephe'/'swisseph' directory at project root. Calculation requires ephemeris files.")
elif swe: # Only set path if swe object exists
    try:
        swe.set_ephe_path(ephe_path)
        logger.info(f"Swisseph path set successfully.")
    except Exception as e:
        logger.critical(f"Failed to set Swisseph path '{ephe_path}': {e}")

# PDF Output Directory Setup
DEFAULT_PDF_OUTPUT_DIR = "./astro_reports_output" # Default relative to where script is run
PDF_OUTPUT_DIR = os.getenv('PDF_OUTPUT_DIR', DEFAULT_PDF_OUTPUT_DIR)
try:
    abs_pdf_output_dir = os.path.abspath(PDF_OUTPUT_DIR)
    os.makedirs(abs_pdf_output_dir, exist_ok=True)
    PDF_OUTPUT_DIR = abs_pdf_output_dir
    logger.info(f"PDF output directory ensured: {PDF_OUTPUT_DIR}")
except OSError as e:
    logger.critical(f"Could not create PDF output dir: {PDF_OUTPUT_DIR}. Error: {e}")
    raise # Stop if output dir cannot be created

# AI Config
AI_MODEL = os.getenv("AI_MODEL", "gpt-4-turbo") # Or your preferred model
try: AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))
except ValueError: AI_TEMPERATURE = 0.3; logger.warning("Invalid AI_TEMPERATURE env var, using 0.3")


# --- Helper Functions ---
# ... (Helper functions like replace_css_variables, _find_tightest_aspect, etc. - assumed identical) ...
def replace_css_variables(svg_content):
    """Replaces CSS variables (var(--name)) with their defined values in SVG content."""
    logger.info("           Parsing CSS variables in SVG...")
    variables = {}
    # Regex to find :root block OR individual variable definitions loosely within braces
    # Group 1 captures the :root block content if matched
    # Group 2 captures the variable name (--var-name) if matched
    # Group 3 captures the variable value if matched
    var_defs = re.findall(r":root\s*{([^}]*)}|{\s*(--[\w-]+)\s*:\s*([^;\}]+?)\s*(?:;|\})", svg_content, re.DOTALL | re.IGNORECASE)

    # Iterate through all matches found by findall
    for root_content, var_name, var_value in var_defs:
        if var_name and var_value:
            # This match tuple came from the second part of the regex | (individual var def)
            variables[var_name.strip()] = var_value.strip()
        elif root_content:
            # This match tuple came from the first part of the regex | (:root block)
            # Need to parse variables within the root_content block separately
            inner_vars = re.findall(r"(--[\w-]+)\s*:\s*([^;\}]+)", root_content)
            for name, value in inner_vars:
                variables[name.strip()] = value.strip()

    if not variables:
        logger.info("             No valid CSS variables found in SVG definition block.")
        return svg_content

    logger.debug(f"             Found CSS variables: {variables}")

    def replacer(match):
        var_name = match.group(1).strip()
        fallback = match.group(2) # Fallback is optional
        resolved_value = variables.get(var_name)

        if resolved_value:
            # logger.debug(f"Replacing {var_name} with {resolved_value}") # Can be noisy
            return resolved_value
        elif fallback:
            fallback_stripped = fallback.strip()
            # Basic check if fallback itself is a variable (not fully recursive)
            if fallback_stripped.lower().startswith("var("):
                logger.warning(f"CSS Variable '{var_name}' not found. Fallback '{fallback_stripped}' is also a variable. Using 'currentColor'.")
                return 'currentColor'
            logger.warning(f"CSS Variable '{var_name}' not found. Using fallback: '{fallback_stripped}'")
            return fallback_stripped
        else:
            logger.warning(f"CSS Variable '{var_name}' not found and no fallback provided. Using 'currentColor'.")
            return 'currentColor'

    # Regex to find var() usages, allowing for optional fallback
    processed_content = re.sub(r'var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\s*\)', replacer, svg_content)
    logger.info("                   CSS variable replacement complete.")
    return processed_content

def _find_tightest_aspect(aspects_dict):
    """Finds the aspect with the smallest orb."""
    logger.debug("Finding tightest aspect...")
    min_orb = 999.0
    tightest = None
    processed_pairs = set() # Track processed pairs (p1, p2, aspect_type) to avoid duplicates

    if not isinstance(aspects_dict, dict):
        logger.warning("Cannot find tightest aspect: Invalid aspects_dict format.")
        return None

    all_aspects = []
    # Consolidate aspects from the defaultdict structure
    for planet_key, aspect_list in aspects_dict.items():
        if isinstance(aspect_list, list):
            all_aspects.extend(aspect_list)

    # Iterate through all collected aspects
    for asp in all_aspects:
        if not isinstance(asp, dict):
            continue
        orb = asp.get("orb")
        p1 = asp.get("planet1")
        p2 = asp.get("planet2")
        aspect_type = asp.get("aspect")

        if orb is None or p1 is None or p2 is None or aspect_type is None:
            continue # Skip invalid aspect entries

        try:
            orb_float = float(orb)
            # Ensure pair key is consistent regardless of planet order
            pair_key = tuple(sorted((p1, p2))) + (aspect_type,)

            # Check if we've already found an aspect of this type for this pair
            if pair_key in processed_pairs:
                continue

            # Found the first occurrence of this aspect type for this pair
            processed_pairs.add(pair_key) # Mark as processed

            # Check if this is the new minimum orb found so far across all pairs/types
            if orb_float < min_orb:
                min_orb = orb_float
                tightest = (p1, aspect_type, p2, orb_float) # Store the details

        except (ValueError, TypeError):
            logger.warning(f"Invalid orb value '{orb}' encountered for aspect {p1}-{aspect_type}-{p2}")
            continue # Skip this aspect if orb is invalid

    if tightest:
        logger.debug(f"Tightest aspect identified: {tightest[0]} {tightest[1]} {tightest[2]} (Orb: {tightest[3]:.2f}°)")
    else:
        logger.debug("No valid aspects found to determine tightest.")
    return tightest

def _format_aspect_for_prompt(aspect_details):
    """Formats the tightest aspect tuple for inclusion in prompts."""
    if aspect_details and len(aspect_details) == 4:
        p1, aspect_type, p2, orb = aspect_details
        return f"{orb:.1f}° {p1} {aspect_type} {p2}"
    return "No specific tight aspect identified"

def _format_detail_string(positions, key):
    """Formats placement details (Sign in House R) for prompts/tables."""
    data = positions.get(key, {})
    # Check if data is a dictionary before accessing keys
    if not isinstance(data, dict):
        logger.debug(f"Cannot format detail string for {key}: Data is not a dictionary.")
        return f"{key} [Details Unavailable]"

    sign = data.get('sign', '?')
    house = data.get('house', '?')

    # Use 0 for house if sign is Error, otherwise use provided house value
    house_display = house if sign not in [None, '?', 'Error'] else 0

    # Check for invalid conditions
    if sign in [None, '?', 'Error'] or house_display in [None, '?', 0, 'Error']: # Check house_display now
        logger.debug(f"Cannot format detail string for {key}: Sign='{sign}', House='{house_display}'")
        # Return just the key if details are missing/invalid
        return f"{key} [Details Unavailable]"

    retro = " R" if data.get('is_retrograde', False) else ""
    return f"{sign} in House {house_display}{retro}"


def _format_balance_data(balance_data, balance_type="elemental"):
    """Formats elemental or modality balance percentages into a string."""
    logger.debug(f"Formatting {balance_type} balance data: {balance_data}")
    if not isinstance(balance_data, dict):
        return f"{balance_type.capitalize()} balance data unavailable."

    total_percent = sum(v for v in balance_data.values() if isinstance(v, (int, float)))
    # Allow a slightly wider tolerance for floating point sums
    if not (98 < total_percent < 102):
        logger.warning(f"Percentages for {balance_type} do not sum close to 100% ({total_percent:.1f}%). Data: {balance_data}")
        # Return an informative error string for the prompt
        return f"[Balance Calculation Error: {balance_type.capitalize()} sum is {total_percent:.1f}%]"

    if balance_type == "elemental":
        items = ["Fire", "Earth", "Air", "Water"]
    elif balance_type == "modality":
        items = ["Cardinal", "Fixed", "Mutable"]
    else:
        return "Unknown balance type"

    formatted_parts = []
    for item in items:
        percent = balance_data.get(item, 0.0) # Default to 0.0 if missing
        try:
            formatted_parts.append(f"{item}: {float(percent):.1f}%")
        except (ValueError, TypeError):
            formatted_parts.append(f"{item}: N/A") # Handle non-numeric values

    return ", ".join(formatted_parts)

def _format_aspect_list(aspect_list, max_aspects=3, aspect_type_filter=None):
    """Formats a list of aspect dictionaries into a summary string for prompts."""
    if not aspect_list or not isinstance(aspect_list, list):
        return "no notable aspects" if not aspect_type_filter else f"no notable {aspect_type_filter} aspects"

    formatted = []
    count = 0
    # Sort by orb to show tightest first
    sorted_aspect_list = sorted(aspect_list, key=lambda x: x.get('orb', 99) if isinstance(x, dict) else 99)

    for asp in sorted_aspect_list:
        if isinstance(asp, dict) and count < max_aspects:
            # Apply type filter if specified
            if aspect_type_filter and asp.get("type") != aspect_type_filter:
                continue

            aspect_type = asp.get("aspect", "?")
            p2 = asp.get("planet2", "?")
            orb = asp.get("orb", "?")
            try:
                orb_str = f"{float(orb):.1f}°"
            except (ValueError, TypeError):
                orb_str = f"{orb}°" # Fallback if orb is not a number

            formatted.append(f"{aspect_type} {p2} ({orb_str})")
            count += 1
        elif count >= max_aspects:
            break # Stop adding once max is reached

    if not formatted:
        return f"no notable {aspect_type_filter} aspects" if aspect_type_filter else "no notable aspects"

    return ", ".join(formatted)

def _format_aspect_patterns(patterns_list): # Changed input from dict to list
    """Formats detected aspect patterns (list of dicts) into a summary string."""
    if not isinstance(patterns_list, list) or not patterns_list: # Check if list is empty
        return "No specific major aspect patterns detected."

    pattern_strings = []
    processed_signatures = set() # Avoid duplicates based on pattern type and points

    for item in patterns_list:
        if isinstance(item, dict):
            pattern_type = item.get('pattern', 'Unknown Pattern')
            points = sorted(item.get('points', [])) # Sort points for consistent signature
            signature = (pattern_type, tuple(points))

            if signature in processed_signatures:
                continue # Skip duplicate pattern configuration

            details = f"{pattern_type} ({', '.join(points)})"
            if 'element' in item: details += f" in {item['element']}"
            if 'sign' in item: details += f" in {item['sign']}"
            if 'house' in item: details += f" in House {item['house']}"
            if 'apex' in item: details += f" [Apex: {item['apex']}]"
            pattern_strings.append(details)
            processed_signatures.add(signature)

    if not pattern_strings:
        return "No specific major aspect patterns detected."
    return "; ".join(pattern_strings)


def _format_future_transits(transits_list, max_transits=5):
    """Formats a list of future transit event dictionaries into a summary string."""
    if not transits_list or not isinstance(transits_list, list):
        return "No significant future transits identified in the next ~12 months."

    formatted = []
    count = 0
    for event in transits_list:
        if isinstance(event, dict) and count < max_transits:
            t_planet = event.get('transiting_planet', '?')
            aspect = event.get('aspect', '?')
            n_point = event.get('natal_point')
            peak_date = event.get('date_peak')
            start_date = event.get('date_start')
            end_date = event.get('date_end')
            date_str = ""
            date_format = '%b %d, %Y' # Example: May 04, 2025

            try:
                # Determine the most relevant date to display
                display_date = peak_date if peak_date else start_date
                if isinstance(display_date, date): # Check if it's a date object
                    date_str = f" (~{display_date.strftime(date_format)})"
                    # Indicate duration if available and dates are valid
                    if isinstance(start_date, date) and isinstance(end_date, date) and start_date != end_date:
                        date_str = f" ({start_date.strftime(date_format)} - {end_date.strftime(date_format)}, peak{date_str})"
                    elif end_date is None and isinstance(start_date, date): # Ongoing aspect
                        date_str = f" (from {start_date.strftime(date_format)} - ongoing)" # Clarify ongoing starts from start_date
                    elif display_date is not None: # Handle case where display_date is not None but also not a date object
                          date_str = " (invalid date type)"
                    # If display_date is None, date_str remains empty ""
                elif display_date is not None: # Handle if display_date is not a date object (e.g., string)
                    date_str = " (date error)"
                # If display_date is None, date_str remains empty ""

            except (AttributeError, ValueError, TypeError) as date_err:
                logger.warning(f"Error formatting date for transit event {event}: {date_err}")
                date_str = " (date format error)"


            if event.get('event_type') == 'Ingress':
                formatted.append(f"{t_planet} {aspect}{date_str}")
            elif n_point: # Aspect event
                formatted.append(f"{t_planet} {aspect.lower()} {n_point}{date_str}")
            else: # Other event type? Log or skip
                logger.debug(f"Skipping formatting for unknown future transit event type: {event.get('event_type')}")
                continue # Skip this event if format is unknown

            count += 1
        elif count >= max_transits:
            if len(transits_list) > max_transits:
                formatted.append("...")
            break

    if not formatted:
        return "No significant future transits identified in the next ~12 months."
    return ", ".join(formatted)


def _get_house_planets(house_num, positions):
    """Gets a list of planets located in a specific house."""
    planets = []
    planets_to_include = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron']
    for planet, data in positions.items():
        if planet in planets_to_include and isinstance(data, dict) and data.get("house") == house_num:
            planets.append(planet)
    return sorted(planets)

# Validator Function (remains the same)
def _validate_context_keys(section_key, prompt_template, context, logger_instance):
    """
    Checks if all keys referenced in a prompt template ({key_name})
    exist in the provided context dictionary. Logs errors for missing keys.
    Returns True if all keys exist, False otherwise. Also returns the count of keys checked.
    """
    if not isinstance(prompt_template, str):
        logger_instance.error(f"[{section_key}] Cannot validate keys: prompt_template is not a string.")
        return False, 0 # Return count 0
    if not isinstance(context, dict):
        logger_instance.error(f"[{section_key}] Cannot validate keys: context is not a dictionary.")
        return False, 0 # Return count 0

    required_keys = set(re.findall(r'\{([a-zA-Z0-9_]+)\}', prompt_template))
    num_keys = len(required_keys) # Get count of keys found in template

    if not required_keys:
        logger_instance.debug(f"[{section_key}] No placeholder keys found in template for validation.")
        return True, num_keys # Return True, count is 0

    missing_keys = []
    for key in required_keys:
        if key not in context:
            missing_keys.append(key)
        # Optional check for empty/placeholder values could go here

    if missing_keys:
        logger_instance.error(f"[{section_key}] Validation FAILED! Missing required context keys: {sorted(list(missing_keys))}")
        return False, num_keys # Return False, and the count of keys checked
    else:
        # Log moved to the calling function to avoid redundancy
        # logger_instance.debug(f"[{section_key}] Context validation passed. All {num_keys} referenced keys found.")
        pass
    return True, num_keys # Return True, and the count of keys checked


# === Context Preparation Logic ==
def _prepare_prompt_context(section_key, chart_data, client_name, gender, occasion_mode, is_pet_report, birth_date=None, birth_time=None, pet_breed=None, pet_species=None, **kwargs):
    """
    Prepares the context dictionary for formatting a specific section's AI prompt.

    Args:
        section_key (str): string identifier for this section
        chart_data (dict): The main chart data dictionary.
        client_name (str): The client or pet name.
        gender (str): Client gender ('M', 'F', or other).
        occasion_mode (str): The report occasion (e.g., 'birthday').
        is_pet_report (bool): Flag indicating if it's a pet report.
        birth_date (str, optional): Birth date string (YYYY-MM-DD). Defaults to None.
        birth_time (str, optional): Birth time string (HH:MM). Defaults to None.
        pet_breed (str, optional): Pet breed. Defaults to None.
        pet_species (str, optional): Pet species. Defaults to None.
        **kwargs: Catch-all for any future or unused fields.
    """
    logger.info(f"--> Preparing context for section: {section_key}")
    # ... function body ...
    context = {}
    if not isinstance(chart_data, dict):
        logger.error(f"Invalid chart_data provided to _prepare_prompt_context for section {section_key}.")
        return {"error": "Invalid chart data"}

    # json_loader is now imported at the top (common.json_loader)
    # The load_json_data function is available if JSON_LOADER_AVAILABLE is True

    default_interp = "[Interpretation data unavailable]"

    # *** UPDATED safe_get_interp with Nested Lookup Logic ***
    def safe_get_interp(group, key, default=default_interp):
        """
        Looks up interpretation, handling normalization, group mapping, and potential nested JSON structures.
        Attempts flat lookup first, then tries nested lookup based on key patterns.
        """
        if not key or not isinstance(key, str) or not group or not isinstance(group, str):
            logger.warning(f"Invalid group ('{group}') or key ('{key}') provided for lookup.")
            return default
        if not JSON_LOADER_AVAILABLE: # Added check
            logger.warning(f"JSON loader not available, cannot lookup {group}/{key}")
            return default # Cannot perform lookup without loader

        # --- Normalization Step ---
        group_norm = group.lower().replace(' ', '_').replace('-', '_')
        key_norm = key.lower().replace(' ', '_').replace('-', '_')

        if key_norm != key or group_norm != group:
            logger.debug(f"Normalized lookup: '{group}/{key}' -> '{group_norm}/{key_norm}'")

        # --- Group to Filename Mapping ---
        file_group = group_norm
        if group_norm in ("major", "minor", "declination"): # Combined aspect groups
            file_group = "aspects"
            logger.debug(f"Mapping group '{group_norm}' to file group '{file_group}')")
        # Add other mappings here if needed (e.g., rising_sign -> rising)
        elif group_norm == "rising_sign":
            file_group = "rising_sign" # Keep mapping explicit if needed, or remove if filename matches
        elif group_norm == "dignity":
            file_group = "dignity" # Adjust if filename is dignities.json -> "dignities"

        # --- Data Loading and Lookup Logic ---
        try:
            # Load the entire data dictionary for the group using the imported function
            full_data = load_json_data(file_group) # Ensure this function works!

            if not isinstance(full_data, dict):
                logger.warning(f"Could not load or parse data for group '{file_group}'. Returning default for key '{key_norm}'.")
                return default

            # 1. Try direct/flat lookup first using the fully combined key
            flat_result = full_data.get(key_norm)
            # Check if result is valid (not None, not empty string, not the default placeholder itself)
            if flat_result is not None and flat_result != "" and flat_result != default_interp:
                logger.debug(f"Flat lookup successful for: {file_group}/{key_norm}")
                return flat_result
            elif flat_result is not None: # It exists but is empty or default
                logger.debug(f"Flat lookup for {file_group}/{key_norm} found but value is empty/default. Will attempt nested.")
            else: # Flat key doesn't exist at all
                logger.debug(f"Flat lookup failed for: {file_group}/{key_norm}. Attempting nested.")


            # 2. Attempt Nested Lookup if flat failed or was empty/default
            parts = key_norm.split('_')
            nested_result = None

            # Try Pattern 1: group_id_subkey (e.g., house_1_corethemes -> data['house_1']['corethemes'])
            if len(parts) >= 3:
                base_key = f"{parts[0]}_{parts[1]}" # e.g., house_1, sun_sign
                sub_key = "_".join(parts[2:])       # e.g., corethemes, aries
                nested_base_obj = full_data.get(base_key)
                if isinstance(nested_base_obj, dict):
                    nested_result = nested_base_obj.get(sub_key)
                    if nested_result is not None and nested_result != "" and nested_result != default_interp:
                        logger.debug(f"Nested lookup successful (Pat1): {file_group}/{base_key}/{sub_key}")
                        return nested_result
                    #else: logger.debug(f"Nested lookup (Pat1) failed for subkey '{sub_key}' within base '{base_key}' in {file_group}") # Can be noisy

            # Try Pattern 2: primary_secondary (e.g., dominant_fire -> data['dominant']['fire'])
            if nested_result is None and len(parts) >= 2:
                base_key = parts[0] # e.g., dominant, lifepath, unaspected, pattern
                sub_key = "_".join(parts[1:]) # e.g., fire, 11, sun, grand_trine
                nested_base_obj = full_data.get(base_key)
                if isinstance(nested_base_obj, dict):
                    nested_result = nested_base_obj.get(sub_key)
                    if nested_result is not None and nested_result != "" and nested_result != default_interp:
                        logger.debug(f"Nested lookup successful (Pat2): {file_group}/{base_key}/{sub_key}")
                        return nested_result
                    #else: logger.debug(f"Nested lookup (Pat2) failed for subkey '{sub_key}' within base '{base_key}' in {file_group}") # Can be noisy

            # 3. If all lookups fail, return the default
            logger.warning(f"Lookup failed for {file_group}/{key_norm} (flat and nested attempts).")
            return default

        # Catch FileNotFoundError specifically if load_json_data raises it (it shouldn't, should return None)
        except FileNotFoundError: # Keep just in case load_json_data changes
            logger.warning(f"Interpretation file not found for group '{file_group}'. Cannot lookup key '{key_norm}'.")
            return default
        # Catch other potential errors during lookup
        except Exception as e:
            logger.error(f"Unexpected error during lookup for {file_group}/{key_norm}: {e}", exc_info=True)
            # Return a more specific error message if possible, otherwise fallback
            return f"[Error Loading: {file_group}/{key_norm}]"
    # *** END of updated safe_get_interp Definition ***


    # --- Extract data safely using .get() with defaults ---
    positions = chart_data.get("positions", {})
    angles = chart_data.get("angles", {})
    birth_details = chart_data.get("birth_details", {})
    chart_signatures = chart_data.get("chart_signatures", {})
    aspects_dict = chart_data.get("aspects", {})
    decl_aspects_dict = chart_data.get("declination_aspects", {})
    numerology_data = chart_data.get("numerology", {})
    earth_energies = chart_data.get("earth_energies", {})
    fixed_star_links = chart_data.get("fixed_star_links", [])
    elemental_balance_data = chart_data.get("elemental_balance", {})
    modality_balance_data = chart_data.get("modality_balance", {})
    house_cusps = chart_data.get("house_info", {}).get("cusps", [])
    aspect_patterns_list = chart_data.get("aspect_patterns", [])
    future_transits = chart_data.get("future_transits", [])
    other_points = chart_data.get("other_points", {})
    midpoints_data = chart_data.get("midpoints", {})
    house_rulers_data = chart_data.get("house_rulers", {})

    # --- Common context ---
    context['client_name'] = client_name
    context['gender'] = gender
    context['age'] = birth_details.get("age", "Unknown")
    context['current_transit_phase'] = chart_data.get("current_transit_phase", "Unknown")
    context['occasion_mode'] = occasion_mode
    context['is_pet_report'] = is_pet_report
    if is_pet_report:
        context['pet_name'] = client_name
        context['species'] = pet_species if pet_species else 'Animal'
        context['breed'] = pet_breed if pet_breed else "Unknown" # Use the passed breed argument, provide default
        context['breed_phrase'] = f" the {pet_breed}" if pet_breed else ""
        logger.debug(f"Pet context added: species={context['species']}, breed={context['breed']}")
    else:
        context['human_name'] = client_name


    # --- JSON Lookups using safe_get_interp ---
    logger.debug("Performing JSON lookups for context...")

    PLANETS_TO_INTERPRET = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron']
    context['all_planet_house_interps_json'] = {}
    context['planet_core_themes_json'] = {}
    dignity_breakdown = {}

    for planet in PLANETS_TO_INTERPRET:
        planet_lower = planet.lower()
        pos_data = positions.get(planet, {})
        sign = pos_data.get('sign')
        house = pos_data.get('house')
        dignity = pos_data.get('dignity')
        house_str = str(house) if house and house != 'Error' and house != 0 else "?"

        sign_key = f"{planet_lower}_sign_{sign.lower()}" if sign and sign != "Error" else None
        context[f'{planet_lower}_sign_interp_json'] = safe_get_interp("planets", sign_key)

        house_key = f"{planet_lower}_house_{house_str}" if house_str != "?" else None
        house_interp = safe_get_interp("planets", house_key)
        context[f'{planet_lower}_house_interp_json'] = house_interp
        if house_key and house_interp != default_interp: # Store only if found
            context['all_planet_house_interps_json'][house_key] = house_interp

        # Dignity Lookup
        dignity_interp = default_interp
        if dignity and dignity != "None" and sign and sign != "Error":
            dignity_lower = dignity.lower()
            dignity_lookup_key = f"{planet_lower}_{dignity_lower}"
            dignity_interp = safe_get_interp("dignity", dignity_lookup_key)
            context[f'{planet_lower}_dignity_interp_json'] = dignity_interp
            if dignity_interp != default_interp:
                dignity_breakdown[planet] = {
                    "type": dignity.capitalize(), "sign": sign.capitalize(), "interpretation": dignity_interp
                }
            else:
                dignity_breakdown[planet] = {
                    "type": dignity.capitalize(), "sign": sign.capitalize(), "interpretation": "[Interpretation text missing]"
                }
        elif dignity and dignity != "None":
             dignity_breakdown[planet] = {
                "type": dignity.capitalize(), "sign": "Unknown", "interpretation": "[Interpretation text missing - Invalid Sign]"
            }
             logger.warning(f"Cannot get dignity interp for {planet} - Sign is missing or invalid: '{sign}'")

        theme_key = f"{planet_lower}_coretheme"
        context['planet_core_themes_json'][planet_lower] = safe_get_interp("planets", theme_key)

    context['venus_core_theme_json'] = context.get('planet_core_themes_json', {}).get('venus', default_interp)
    context['chiron_core_theme_json'] = context.get('planet_core_themes_json', {}).get('chiron', default_interp)

    # Asteroids
    ASTEROIDS_TO_INTERPRET = ["Ceres", "Pallas", "Juno", "Vesta"]
    for asteroid in ASTEROIDS_TO_INTERPRET:
        asteroid_lower = asteroid.lower()
        pos_data = positions.get(asteroid, {})
        sign = pos_data.get('sign')
        house = pos_data.get('house')
        house_str = str(house) if house and house != 'Error' and house != 0 else "?"
        sign_key = f"{asteroid_lower}_sign_{sign.lower()}" if sign and sign != "Error" else None
        context[f'{asteroid_lower}_sign_interp_json'] = safe_get_interp("asteroids", sign_key)
        house_key = f"{asteroid_lower}_house_{house_str}" if house_str != "?" else None
        context[f'{asteroid_lower}_house_interp_json'] = safe_get_interp("asteroids", house_key)
        theme_key = f"{asteroid_lower}_coretheme"
        context[f'{asteroid_lower}_core_theme_json'] = safe_get_interp("asteroids", theme_key)

    # House Cusps
    HOUSE_NUMBERS = range(1, 13)
    for house_num in HOUSE_NUMBERS:
        house_key_prefix = f"house_{house_num}"
        cusp_sign = chart_data.get('house_rulers', {}).get(f'House {house_num}', {}).get('sign', '?')
        cusp_sign_key = f"{house_key_prefix}_sign_{cusp_sign.lower()}" if cusp_sign and cusp_sign != "Error" and cusp_sign != "?" else None
        context[f'{house_key_prefix}_sign_interp_json'] = safe_get_interp("house", cusp_sign_key)
        theme_key = f"{house_key_prefix}_corethemes"
        context[f'{house_key_prefix}_core_themes_json'] = safe_get_interp("house", theme_key)
        context[f'{house_key_prefix}_cusp_sign'] = cusp_sign

    # Angles (Rising Sign)
    asc_data = positions.get("Ascendant", {})
    if not asc_data: asc_data = angles.get("Ascendant", {})
    asc_sign = asc_data.get('sign')
    context['asc_sign'] = asc_sign if asc_sign and asc_sign != "Error" else "?"
    rising_data = load_json_data("rising_sign")
    if isinstance(rising_data, dict):
        context["asc_sign_interp_json"] = rising_data.get(asc_sign, default_interp)
        if context["asc_sign_interp_json"] == default_interp and asc_sign != '?':
             logger.warning(f"Interpretation for Ascendant sign '{asc_sign}' not found in rising_sign.json.")
    else:
        logger.warning("Failed to load 'rising_sign.json' data. Ascendant interpretation unavailable.")
        context["asc_sign_interp_json"] = default_interp

    # Nodes
    NODE_TYPES = ["North", "South"]
    for node_type in NODE_TYPES:
        node_name = f"{node_type} Node"
        node_prefix = node_type.lower() + "node"
        pos_data = positions.get(node_name, {})
        sign = pos_data.get('sign')
        house = pos_data.get('house')
        house_str = str(house) if house and house != 'Error' and house != 0 else "?"
        sign_key = f"{node_prefix}_sign_{sign.lower()}" if sign and sign != "Error" else None
        context[f'{node_prefix}_sign_interp_json'] = safe_get_interp("nodes", sign_key)
        house_key = f"{node_prefix}_house_{house_str}" if house_str != "?" else None
        context[f'{node_prefix}_house_interp_json'] = safe_get_interp("nodes", house_key)

    # Numerology
    lp_num = numerology_data.get("Life Path Number", {}).get("number", '?')
    py_num = numerology_data.get("Personal Year", {}).get("number", '?')
    su_num = numerology_data.get("Soul Urge Number", {}).get("number", '?')
    ex_num = numerology_data.get("Expression Number", {}).get("number", '?')
    lp_key = f"lifepath_{lp_num}" if lp_num not in [None, "?", "N/A", 0] else None
    context['lp_interp_json'] = safe_get_interp("numerology", lp_key)
    py_key = f"personalyear_{py_num}" if py_num not in [None, "?", "N/A", 0] else None
    context['py_interp_json'] = safe_get_interp("numerology", py_key)
    su_key = f"soulurge_{su_num}" if su_num not in [None, "?", "N/A", 0] else None
    context['su_interp_json'] = safe_get_interp("numerology", su_key)
    ex_key = f"expression_{ex_num}" if ex_num not in [None, "?", "N/A", 0] else None
    context['ex_interp_json'] = safe_get_interp("numerology", ex_key)

    # Balance & Dominants/Weakest Themes
    dom_elem = chart_signatures.get("dominant_element", "?")
    weak_elem = chart_signatures.get("weakest_element", "?")
    dom_mod = chart_signatures.get("dominant_modality", "?")
    weak_mod = chart_signatures.get("weakest_modality", "?")
    context['weakest_modality'] = weak_mod
    dom_elem_key = f"dominant_{dom_elem.lower()}" if dom_elem not in ["?", "None", "Error", "N/A (Only Dominant Present)"] else None
    context['dom_elem_interp_json'] = safe_get_interp("element", dom_elem_key)
    weak_elem_key = f"weakest_{weak_elem.lower()}" if weak_elem not in ["?", "None", "Error", "N/A (Only Dominant Present)"] else None
    context['weak_elem_interp_json'] = safe_get_interp("element", weak_elem_key)
    dom_mod_key = f"dominant_{dom_mod.lower()}" if dom_mod not in ["?", "None", "Error", "N/A (Only Dominant Present)"] else None
    context['dom_mod_interp_json'] = safe_get_interp("modality", dom_mod_key)
    weak_mod_key = f"weakest_{weak_mod.lower()}" if weak_mod not in ["?", "None", "Error", "N/A (Only Dominant Present)"] else None
    context['weak_mod_interp_json'] = safe_get_interp("modality", weak_mod_key)
    combo_key = f"{dom_elem.lower()}_{dom_mod.lower()}" if dom_elem not in ["?", "None", "Error"] and dom_mod not in ["?", "None", "Error"] else None
    context['dominant_combo_interp_json'] = safe_get_interp("dominant", combo_key)

    def get_themes(balance_type, category_str):
        themes = []
        if category_str not in [None, "?", "N/A (Only Dominant Present)"]:
            for cat in category_str.split('/'):
                cat_strip = cat.strip()
                cat_lower = cat_strip.lower()
                if not cat_lower or cat_strip == "None": continue
                theme_lookup_key = f"{cat_lower}_core_themes"
                theme_data = safe_get_interp(balance_type, theme_lookup_key, default=None)
                if theme_data is None:
                    cat_data = safe_get_interp(balance_type, cat_lower, default=None)
                    if isinstance(cat_data, dict):
                        theme_data = cat_data.get('core_themes', default_interp)
                    else:
                        theme_data = default_interp
                themes.append(theme_data if theme_data else default_interp)
        return " / ".join(themes) if themes else default_interp

    context["dominant_element_themes_json"] = get_themes("element", dom_elem)
    context["weakest_element_themes_json"] = get_themes("element", weak_elem)
    context["dominant_modality_themes_json"] = get_themes("modality", dom_mod)
    context["weakest_modality_themes_json"] = get_themes("modality", weak_mod)

    # Aspects List
    all_aspect_interps = []; major_aspect_interps = []; minor_aspect_interps = []; decl_aspect_interps = []; unaspected_interps = []
    processed_aspect_keys = set()
    all_calculated_aspects_list = []
    if isinstance(aspects_dict, dict):
        for asp_list in aspects_dict.values():
            if isinstance(asp_list, list): all_calculated_aspects_list.extend(asp_list)
    if isinstance(decl_aspects_dict, dict):
        for decl_asp_list in decl_aspects_dict.values():
            if isinstance(decl_asp_list, list): all_calculated_aspects_list.extend(decl_asp_list)

    for asp in all_calculated_aspects_list:
        if not isinstance(asp, dict): continue
        p1 = asp.get("planet1"); p2 = asp.get("planet2"); aspect_type = asp.get("aspect"); orb = asp.get("orb"); type_group = asp.get("type")
        if p1 and p2 and aspect_type and type_group:
            sorted_p1, sorted_p2 = sorted((p1, p2))
            lookup_key = f"{sorted_p1.lower()}_{sorted_p2.lower()}_{aspect_type.lower()}"
            group_name = type_group
            if (group_name, lookup_key) not in processed_aspect_keys:
                interp = safe_get_interp(group_name, lookup_key)
                processed_aspect_keys.add((group_name, lookup_key))
                if interp != default_interp:
                    aspect_interp_data = {'planet1': p1, 'planet2': p2, 'aspect': aspect_type, 'orb': orb, 'type': type_group, 'interpretation': interp }
                    all_aspect_interps.append(aspect_interp_data)
                    if type_group == 'major': major_aspect_interps.append(aspect_interp_data)
                    elif type_group == 'declination': decl_aspect_interps.append(aspect_interp_data)
                    elif type_group == 'minor': minor_aspect_interps.append(aspect_interp_data)

    context['all_aspect_interps_json'] = json.dumps(all_aspect_interps)
    context['major_aspect_interps_json'] = json.dumps(major_aspect_interps)
    context['minor_aspect_interps_json'] = json.dumps(minor_aspect_interps)
    context['declination_aspect_interps_json'] = json.dumps(decl_aspect_interps)

    # Unaspected planets
    unaspected_planets_raw = chart_signatures.get("unaspected_planets_str", "")
    unaspected_planets = [p.strip() for p in unaspected_planets_raw.split(",") if p.strip() and p.strip().lower() != "none"]
    for planet in unaspected_planets:
        lookup_key = f"unaspected_{planet.lower()}"
        interp = safe_get_interp("unaspected", lookup_key)
        if interp != default_interp:
            unaspected_interps.append({'planet': planet, 'interpretation': interp})
    context['unaspected_interps_json'] = json.dumps(unaspected_interps)

    # Midpoints List
    midpoint_interps = []
    if isinstance(midpoints_data, dict):
        for mp_key, mp_data in midpoints_data.items():
            if isinstance(mp_data, dict) and mp_data.get('degree') is not None:
                mp_names = mp_key.split("/")
                if len(mp_names) == 2:
                    sorted_mp1, sorted_mp2 = sorted(mp_names)
                    lookup_key = f"midpoint_{sorted_mp1.lower()}_{sorted_mp2.lower()}"
                    interp = safe_get_interp("midpoint", lookup_key)
                    if interp != default_interp:
                        midpoint_interps.append({'midpoint': mp_key, 'degree': mp_data['degree'], 'sign': mp_data.get('sign'), 'house': mp_data.get('house'), 'interpretation': interp})
                else: logger.warning(f"Skipping midpoint '{mp_key}': Unexpected key format.")
    context['midpoint_interps_json'] = json.dumps(midpoint_interps)

    # Aspect Patterns List
    aspect_pattern_interps = []
    if isinstance(aspect_patterns_list, list):
        for pattern_instance in aspect_patterns_list:
            if isinstance(pattern_instance, dict):
                pattern_type = pattern_instance.get('pattern')
                if pattern_type:
                    lookup_key = f"pattern_{pattern_type.replace(' ', '_').lower()}"
                    interp = safe_get_interp("aspect_patterns", lookup_key)
                    if interp != default_interp:
                        aspect_pattern_interps.append({'pattern_type': pattern_type, 'instance_details': pattern_instance, 'interpretation': interp})
    context['aspect_pattern_interps_json'] = json.dumps(aspect_pattern_interps)

    # Arabic Parts List
    arabic_part_interps = []
    ARABIC_PARTS_NAMES = ["Part of Fortune", "Part of Spirit"]
    if isinstance(other_points, dict):
        for part_name in ARABIC_PARTS_NAMES:
            part_data = other_points.get(part_name, {})
            if isinstance(part_data, dict) and part_data.get('degree') is not None:
                part_sign = part_data.get('sign', '?'); part_house = part_data.get('house', '?'); house_str = str(part_house) if part_house and part_house != 'Error' and part_house != 0 else "?"
                part_name_key = part_name.lower().replace("part of ", "pof_").replace(" ", "_")
                lookup_keys_to_try = [
                    f"{part_name_key}_sign_{part_sign.lower()}_house_{house_str}" if part_sign != '?' and house_str != '?' else None,
                    f"{part_name_key}_sign_{part_sign.lower()}" if part_sign != '?' else None,
                    f"{part_name_key}_house_{house_str}" if house_str != '?' else None,
                    f"{part_name_key}"
                ]
                interp = default_interp
                for key_attempt in lookup_keys_to_try:
                    if key_attempt:
                        current_interp = safe_get_interp("arabic_parts", key_attempt)
                        if current_interp != default_interp:
                            interp = current_interp
                            break
                if interp != default_interp:
                    arabic_part_interps.append({'part': part_name, 'degree': part_data['degree'], 'sign': part_sign, 'house': part_house, 'interpretation': interp})
    context['arabic_part_interps_json'] = json.dumps(arabic_part_interps)

    # Moon Phase Interp
    moon_phase_name = earth_energies.get("moon_phase", {}).get("name", "?")
    moon_phase_key = f"moonphase_{moon_phase_name.replace(' ', '_').lower()}" if moon_phase_name and moon_phase_name != "Error" and moon_phase_name != "?" else None
    context['moon_phase_json'] = safe_get_interp("moon_phases", moon_phase_key)

    # Calculated/Formatted Strings
    context['tightest_aspect_str'] = _format_aspect_for_prompt(_find_tightest_aspect(aspects_dict))
    chart_ruler_planet = birth_details.get('chart_ruler', '?')
    context['chart_ruler_planet'] = chart_ruler_planet
    context['chart_ruler_details_str'] = _format_detail_string(positions, chart_ruler_planet)
    context['chart_ruler_house'] = positions.get(chart_ruler_planet, {}).get('house', '?')
    cr_house = context['chart_ruler_house']
    cr_house_str = str(cr_house) if cr_house and cr_house != '?' else "?"
    cr_house_key = f"{chart_ruler_planet.lower()}_house_{cr_house_str}" if cr_house_str != "?" and chart_ruler_planet not in [None, '?', 'Error'] else None
    context['chart_ruler_interp_json'] = safe_get_interp("planets", cr_house_key)

    # Planet Retrograde Dict
    planet_retrograde_dict = {}
    positions_data_for_retro = chart_data.get("positions", {})
    if isinstance(positions_data_for_retro, dict):
        for planet_name, data in positions_data_for_retro.items():
            planets_to_check_retro = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron']
            if planet_name in planets_to_check_retro and isinstance(data, dict):
                is_retro = data.get('is_retrograde', False)
                planet_retrograde_dict[planet_name.lower()] = is_retro
    context['planet_retrograde'] = planet_retrograde_dict
    logger.debug(f"Built planet_retrograde dictionary: {planet_retrograde_dict}")

    # Star Sign Logic
    context['star_sign'] = "None" # Default if no stars
    if fixed_star_links:
        try:
            # Assuming fixed_star_links structure is like [{'star': 'Name', 'orb': 1.23, 'sign': 'Aries', ...}]
            valid_stars = [star for star in fixed_star_links if isinstance(star, dict) and 'orb' in star and isinstance(star['orb'], (float, int))]
            if valid_stars:
                tightest_star_info = min(valid_stars, key=lambda s: s['orb'])
                # Use sign from the tightest star info
                context['star_sign'] = tightest_star_info.get('star_sign', "Error: Sign Key Missing")
                logger.debug(f"Determined star_sign '{context['star_sign']}' from tightest orb star: {tightest_star_info.get('star', '?')}")
            else:
                logger.warning("No valid fixed star entries with orb found in fixed_star_links.")
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Could not determine tightest fixed star due to error: {e}")
            context['star_sign'] = "Error: Calculation Failed"
    else:
        logger.debug("No fixed star links provided in chart_data.")

    # Finalize Dignity Breakdown JSON
    if dignity_breakdown:
        logger.info(f"Generated dignity breakdown for {len(dignity_breakdown)} planets.")
        context['dignity_breakdown_json'] = json.dumps(dignity_breakdown, indent=2)
    else:
        logger.warning("No dignity data found or processed for breakdown.")
        context['dignity_breakdown_json'] = json.dumps({})

    # Other Formatted Strings
    context["elemental_balance_str"] = _format_balance_data(elemental_balance_data, "elemental")
    context["modality_balance_str"] = _format_balance_data(modality_balance_data, "modality")
    context["dominant_element"] = chart_signatures.get("dominant_element", "?")
    context["weakest_element"] = chart_signatures.get("weakest_element", "?")
    context["dominant_modality"] = chart_signatures.get("dominant_modality", "?")
    context['unaspected_planets_str'] = chart_signatures.get("unaspected_planets_str", "None")
    for h_num in [2, 6, 7, 10, 12]:
        planets_in_house = _get_house_planets(h_num, positions)
        context[f'house_{h_num}_planets_str'] = ", ".join(planets_in_house) if planets_in_house else "None"
    context['mc_sign'] = angles.get('Midheaven', {}).get('sign', '?')
    context['future_transits_str'] = _format_future_transits(future_transits, max_transits=5)

    # Populate simple sign/house/retrograde keys
    all_points_for_details = PLANETS_TO_INTERPRET + ASTEROIDS_TO_INTERPRET + ['Ascendant', 'Midheaven', 'North Node', 'South Node', 'Part of Fortune', 'Part of Spirit']
    for p in all_points_for_details:
        p_lower = p.lower().replace(" ", "_")
        if p in ['Ascendant', 'Midheaven']: pos_data = angles.get(p, {})
        elif p in ['Part of Fortune', 'Part of Spirit']: pos_data = other_points.get(p, {})
        else: pos_data = positions.get(p, {})
        context[f'{p_lower}_sign'] = pos_data.get('sign', '?')
        context[f'{p_lower}_house'] = pos_data.get('house', '?')
        context[f'{p_lower}_retrograde'] = "(R)" if pos_data.get('is_retrograde', False) else ""

    # Populate simple numerology/earth energy keys
    context['life_path_num'] = lp_num
    context['personal_year_num'] = py_num
    context['soul_urge_num'] = su_num if su_num != 0 else '?'
    context['expression_num'] = ex_num if ex_num != 0 else '?'
    context['schumann_resonance'] = earth_energies.get('schumann', {}).get('frequency', 'N/A')
    context['moon_phase_name'] = earth_energies.get('moon_phase', {}).get('name', '?')
    context['birth_location'] = f"{birth_details.get('city', '?')}, {birth_details.get('country', '?')}"
    context['hemisphere'] = birth_details.get('hemisphere', 'Unknown')
    context['structured_fixed_star_data_json'] = json.dumps(fixed_star_links) if fixed_star_links else "[]"

    # Populate simple aspect string keys
    context['pluto_aspects_str'] = _format_aspect_list(aspects_dict.get("Pluto", []), max_aspects=2, aspect_type_filter='major')
    context['mc_aspects_str'] = _format_aspect_list(aspects_dict.get("Midheaven", []), max_aspects=2, aspect_type_filter='major')
    context['moon_aspects_str'] = _format_aspect_list(aspects_dict.get("Moon", []), max_aspects=3)

    # Validator Call
    PROMPTS_TO_USE = PET_PROMPTS if is_pet_report else HUMAN_PROMPTS
    base_prompt_template_for_validation = "" # Initialize
    num_keys_for_validation = 0 # Initialize

    # Find the prompt template for the current section_key
    # Assuming PROMPTS_TO_USE is a list of dicts, each with 'section_id' and 'ai_prompt'
    if isinstance(PROMPTS_TO_USE, list):
        for p_struct in PROMPTS_TO_USE:
            if isinstance(p_struct, dict) and p_struct.get("section_id") == section_key:
                base_prompt_template_for_validation = p_struct.get("ai_prompt", "")
                break # Found the section
    # Remove the fallback for dict structure as PROMPTS are lists now
    # elif isinstance(PROMPTS_TO_USE, dict): # Old structure fallback removed
    #      base_prompt_template_for_validation = PROMPTS_TO_USE.get(section_key, {}).get("ai_prompt", "")

    if base_prompt_template_for_validation:
        validation_passed, num_keys_for_validation = _validate_context_keys(section_key, base_prompt_template_for_validation, context, logger) # Pass global logger
        if not validation_passed:
            context['validation_error'] = True
            # Error already logged by validator
            # logger.error(f"Context for section '{section_key}' failed validation due to missing keys (checked {num_keys_for_validation} keys).")
        else:
             logger.debug(f"[{section_key}] Context validation passed. All {num_keys_for_validation} referenced keys found.")
    else:
        # Only log error if it's NOT a section expected to skip AI
        sections_expected_to_skip_ai = ["cover", "toc", "chart_wheel"] # Match this list with generate_report_content_via_ai
        if section_key not in sections_expected_to_skip_ai:
            logger.warning(f"[{section_key}] Could not find base prompt template in PROMPTS_TO_USE for validation (or section skips AI).")
            # Decide if this should be an error or just a warning
            # context['validation_error'] = True # Optionally flag validation error if template missing for AI section
            # logger.error(f"[{section_key}] No base prompt template found in PROMPTS_TO_USE for section expecting AI.")
        else:
            logger.debug(f"[{section_key}] No base prompt template needed/found for validation (section skips AI).")


    return context


# --- Content Generation Function ---
# ... (Full function definition from previous version) ...
def generate_report_content_via_ai(
    chart_data, client_name, gender,
    client_instance, # Renamed to avoid conflict with global `client`
    test_mode_flag, # Renamed
    prompts_list, # Renamed for clarity
    occasion_mode="default",
    is_pet_report=False,
    pet_breed=None,
    pet_species=None
):
    """Loops through PROMPTS (list), prepares context, formats, calls AI or stubs, returns full results dict."""
    if not isinstance(prompts_list, list) or not prompts_list:
        logger.critical("PROMPTS list is not available or invalid.")
        return {"error": "PROMPTS list not loaded or invalid format"}

    report_sections_final = {}
    logger.info(f"Starting content generation loop for {len(prompts_list)} sections...")

    system_prompt_elowen = """You are Elowen, a wise, empathetic, and insightful astrologer with deep knowledge of esoteric traditions, mythology, and psychological archetypes. Your writing style is poetic, evocative, and empowering, using a direct second-person voice (addressing the client as 'you'). You seamlessly blend technical astrological details and provided interpretations with rich, symbolic narrative. Avoid generic statements; ensure every insight expands upon the specific chart data and interpretations provided in the prompt. Do not use markdown formatting like ### or * in your response; use plain text headers where requested."""
    system_prompt_mika = """You are Mika, a whimsical, heartful guide who speaks to and about animals with warmth, curiosity, and respect. Your voice is affectionate, playful, and sometimes soul-deep, always addressing the animal's human guardian. You use clear metaphors and simple language to explain astrology. If appropriate, weave in animal instincts, loyalty, curiosity, or spiritual symbolism. Avoid overly complex or abstract language. Ensure the tone is consistently lighthearted and humorous for a pet report."""

    current_persona = "Mika" if is_pet_report else "Elowen"
    current_system_prompt = system_prompt_mika if is_pet_report else system_prompt_elowen
    logger.info(f"Using persona: {current_persona}")

    prompt_context = {} # Initialize context dictionary outside the loop for potential reuse/access in blessing

    for prompt_struct in prompts_list:
        section_key = prompt_struct.get("section_id")
        if not section_key:
             logger.warning("Skipping prompt structure with missing 'section_id'.")
             continue

        if not isinstance(prompt_struct, dict):
            logger.warning(f"Skipping invalid prompt structure for key: {section_key}")
            continue

        logger.info(f"Processing section: {section_key} - {prompt_struct.get('header', 'No Header')}")
        final_section_data = copy.deepcopy(prompt_struct)
        ai_generated_content = f"[AI Placeholder - {section_key}]"
        error_flag = False
        section_meta = final_section_data.get("meta", {})

        sections_to_skip_ai = ["cover", "toc", "chart_wheel"]
        should_skip_ai = section_meta.get("skip_ai", False) or section_key in sections_to_skip_ai

        if should_skip_ai:
            if section_key in sections_to_skip_ai:
                 ai_generated_content = f"[{section_key.replace('_', ' ').title()} Section - Not AI Generated]"
            else:
                 ai_generated_content = "[AI Generation Skipped]"
            logger.info(f"           -> Skipping AI for {section_key} (Marked as skip_ai or special section)")
        else:
            base_prompt = final_section_data.get("ai_prompt", "")
            if not base_prompt or len(base_prompt.strip()) < 10:
                ai_generated_content = "[Invalid Prompt Template]"
                error_flag = True
                logger.error(f"Invalid or missing prompt template for {section_key}")
            else:
                prompt_context = _prepare_prompt_context(section_key, chart_data, client_name, gender, occasion_mode, is_pet_report, pet_breed, pet_species)

                if prompt_context.get('validation_error'):
                    ai_generated_content = f"[SYSTEM ERROR: Context Validation Failed for {section_key} - Check Logs]"
                    error_flag = True
                elif "error" in prompt_context:
                    ai_generated_content = f"[SYSTEM ERROR: Context Prep Failed for {section_key}: {prompt_context.get('error')}]"
                    error_flag = True
                    logger.error(f"Context preparation failed for {section_key}: {prompt_context.get('error')}")
                else:
                    try:
                        voiced_prompt_template = apply_voice_to_prompt(
                            base_prompt=base_prompt, persona=current_persona,
                            tactics=section_meta.get("tactics"), directive=section_meta.get("directive"),
                            theme=section_meta.get("theme"), tone_mode=section_meta.get("tone_mode", "default"),
                            include_journal_prompt=section_meta.get("include_journal_prompt", False),
                            clarity_first=section_meta.get("clarity_first", True),
                            client_name=client_name, # Pass client name
                            species=pet_species # Pass species for voice engine
                        )
                    except Exception as voice_err:
                        ai_generated_content = f"[SYSTEM ERROR: Voice Application Failed]"
                        error_flag = True
                        logger.error(f"Error applying voice for {section_key}: {voice_err}", exc_info=True)
                        voiced_prompt_template = base_prompt

                    if not error_flag:
                        try:
                            formatted_ai_prompt = voiced_prompt_template.format(**prompt_context)
                            logger.debug(f"Formatted Prompt (start) {section_key}: {formatted_ai_prompt[:300]}...")
                            # Placeholder check (adjust filter as needed)
                            unresolved = re.findall(r'(\{.*?\})', formatted_ai_prompt)
                            unresolved_filtered = [p for p in unresolved if not (p.endswith(('_json}', '_str}', 'sign}', 'house}', '_num}', 'resonance}')) or p in ['{pet_name}', '{human_name}', '{species}', '{breed_phrase}'])] # Adjusted filter
                            if unresolved_filtered:
                                logger.warning(f"Potential unresolved placeholders in {section_key}: {unresolved_filtered[:5]}...")
                        except KeyError as e:
                            ai_generated_content = f"[SYSTEM ERROR: Missing key '{e}' during formatting]"
                            error_flag = True
                            logger.error(f"Placeholder error {section_key}: Missing key {e}.")
                        except Exception as fmt_err:
                            ai_generated_content = f"[SYSTEM ERROR: Formatting failed]"
                            error_flag = True
                            logger.error(f"Format error {section_key}: {fmt_err}", exc_info=True)

                        if not error_flag:
                            if test_mode_flag or client_instance is None: # Use renamed vars
                                ai_generated_content = (f"**[TEST MODE ACTIVE - AI Call Mocked]**\n\n_(Prompt for '{section_key}'):_\n{formatted_ai_prompt[:800]}...")
                                logger.info(f"             -> MOCK Generated for {section_key}")
                            else:
                                logger.info(f"                         ▶️ Calling AI ({AI_MODEL}) for {section_key}...")
                                try:
                                    messages=[{"role": "system", "content": current_system_prompt},{"role": "user", "content": formatted_ai_prompt}]
                                    response = client_instance.chat.completions.create(model=AI_MODEL, messages=messages, temperature=AI_TEMPERATURE) # Use client_instance
                                    ai_response_text = response.choices[0].message.content.strip()
                                    ai_generated_content = ai_response_text if ai_response_text else "[AI Response Empty]";
                                    if not ai_response_text: logger.warning(f"Empty AI response for {section_key}.")
                                    logger.info(f"             -> AI Response received for {section_key} ({len(ai_generated_content)} chars)")
                                except AuthenticationError as auth_err:
                                    logger.error(f"AUTH ERROR '{section_key}': {auth_err}.")
                                    ai_generated_content = f"[ERROR: OpenAI Auth Error]"
                                    error_flag = True
                                except OpenAIError as api_err:
                                    logger.error(f"API Error '{section_key}': {api_err}")
                                    ai_generated_content = f"[ERROR: OpenAI API Error - Code: {getattr(api_err, 'code', 'N/A')}]"
                                    error_flag = True
                                except Exception as call_err:
                                    logger.error(f"Unexpected AI Call Error '{section_key}': {call_err}", exc_info=True)
                                    ai_generated_content = f"[ERROR: Unexpected API Call Error]"
                                    error_flag = True

        # --- Append Pet Blessing ---
        # Logic remains the same, but ensure prompt_context is accessible
        if is_pet_report and section_key == "05_Final_Pet_Message" and not error_flag: # Check specific section key
             logger.debug("Attempting to append pet blessing...")
             if PET_BLESSINGS:
                 bless_data = PET_BLESSINGS.get(occasion_mode, PET_BLESSINGS.get("pet_default", {}))
                 blessing_text_template = bless_data.get("blessing", "")
                 if blessing_text_template:
                     try:
                         # Use pet_name from prompt_context if available, otherwise default name
                         pet_name_for_blessing = prompt_context.get("pet_name", client_name) if isinstance(prompt_context, dict) else client_name
                         final_blessing_text = blessing_text_template.replace("{pet_name}", pet_name_for_blessing)
                         if isinstance(ai_generated_content, str):
                             if ai_generated_content.strip() != f"[AI Placeholder - {section_key}]":
                                 ai_generated_content += "\n\n---\n\n"
                             ai_generated_content += final_blessing_text
                             logger.debug("Appended pet blessing.")
                         else: logger.warning("Cannot append blessing, AI content not string.")
                     except Exception as bless_fmt_err:
                         logger.error(f"Error formatting/appending pet blessing: {bless_fmt_err}", exc_info=True)
                         if isinstance(ai_generated_content, str): ai_generated_content += "\n\n[Error formatting blessing]"
                 else: logger.warning(f"No blessing text for occasion '{occasion_mode}' or default in PET_BLESSINGS.")
             else: logger.warning("PET_BLESSINGS data not loaded or is empty.")

        final_section_data['ai_generated_content'] = ai_generated_content
        final_section_data['error_flag'] = error_flag
        report_sections_final[section_key] = final_section_data
        logger.debug(f"Finished processing section {section_key}. Error: {error_flag}")

    logger.info("AI content generation loop finished.")
    return report_sections_final


# --- Placeholder Validation Function ---
# ... (Full function definition from previous version) ...
def validate_generated_content(report_content):
    """Placeholder validation function."""
    logger.debug("Running placeholder content validation...")
    issues_found = 0
    if not isinstance(report_content, dict):
        logger.error("Validation Error: report_content is not a dictionary.")
        return False, 1 # Indicate failure and one issue

    for section_key, section_data in report_content.items():
        if not isinstance(section_data, dict):
            logger.warning(f"Validation Issue ({section_key}): Section data is not a dictionary.")
            issues_found += 1
            continue # Skip further checks for this section

        content = section_data.get('ai_generated_content')
        error_flag = section_data.get('error_flag')

        if error_flag:
            logger.warning(f"Validation Issue ({section_key}): Error flag is set.")
            issues_found += 1

        if content is None:
            logger.warning(f"Validation Issue ({section_key}): 'ai_generated_content' key is missing.")
            issues_found += 1
        elif not isinstance(content, str):
            logger.warning(f"Validation Issue ({section_key}): 'ai_generated_content' is not a string.")
            issues_found += 1
        # Check for specific error placeholders generated by the script itself
        elif "[SYSTEM ERROR" in content or "[ERROR:" in content or "[Interpretation data unavailable]" in content or "[Invalid Prompt Template]" in content:
             # Exclude cases where these are expected placeholders for skipped sections
             sections_to_skip_ai = ["cover", "toc", "chart_wheel"]
             # Check if the content matches one of the expected placeholders *and* the section is in the skip list
             is_expected_placeholder = any(content.strip() == f"[{s.replace('_', ' ').title()} Section - Not AI Generated]" for s in sections_to_skip_ai)
             is_explicitly_skipped_meta = section_data.get("meta", {}).get("skip_ai", False) and content.strip() == "[AI Generation Skipped]"

             if not (is_expected_placeholder or is_explicitly_skipped_meta):
                 logger.warning(f"Validation Issue ({section_key}): Content contains error or unexpected placeholder indicators.")
                 # Consider being more specific based on the exact text if needed
                 issues_found += 1
             else:
                 logger.debug(f"Validation check: Skipping expected placeholder content for {section_key}.")

        # Add check for empty/very short content, exclude sections known to be short or placeholders
        # Updated check to use section_id from the prompt_struct within section_data
        elif len(content.strip()) < 10 and not (section_data.get("section_id") in ["cover", "toc", "chart_wheel"] or section_data.get("meta", {}).get("skip_ai")):
             # Check if it's a numerical section key that isn't typically short
             try:
                 # Assuming numerical prefixes like "01_", "02_", etc.
                 prefix = section_key.split('_')[0]
                 if prefix.isdigit():
                     # You might define a threshold for minimum expected length here per section type or generally
                     # For now, a simple check for very short non-skipped, non-special sections
                     logger.warning(f"Validation Issue ({section_key}): Generated content seems very short ({len(content.strip())} chars) for a non-skipped section.")
                     issues_found += 1
                 else:
                     logger.debug(f"Validation check: Skipping short content check for non-numerical section key {section_key}.") # Handle non-numerical sections
             except IndexError:
                  logger.debug(f"Validation check: Skipping short content check for section key {section_key} (no numerical prefix).") # Handle keys with no underscore


    logger.debug(f"Placeholder validation finished. Found {issues_found} potential issues.")
    # Only consider validation truly "passed" if no issues were found
    return issues_found == 0, issues_found

# --- Main Workflow Function ---
# ... (Full function definition from previous version, including call to corrected generate_human_pdf) ...
def main(birth_info_for_calc, client_name, gender, occasion_mode="default", full_name=None, is_pet_report=False, pet_breed=None, pet_species=None, output_path=None):
    """Orchestrates the entire report generation process."""
    global KerykeionClass, ChartMakerClass, client, __version__, OCCASION_STYLES_FROM_ORCHESTRATOR
    report_script_version = __version__
    logger.info(f"🚀 Starting Report Generation (V{report_script_version}) for: {client_name}...")
    logger.info(f"Report Type: {'Pet' if is_pet_report else 'Human'}, Occasion: {occasion_mode}")
    if is_pet_report: logger.info(f"Pet Species: {pet_species if pet_species else 'Unknown'}, Breed: {pet_breed if pet_breed else 'Unknown'}");
    start_time = datetime.now()

    # Select the correct PROMPTS list based on is_pet_report
    PROMPTS_TO_USE = PET_PROMPTS if is_pet_report else HUMAN_PROMPTS
    logger.info(f"Loading {'pet' if is_pet_report else 'human'} prompts.")
    if not isinstance(PROMPTS_TO_USE, list) or not PROMPTS_TO_USE:
        logger.critical("FATAL: No valid prompt definitions loaded for selected type. Aborting.")
        return

    safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_") or "UnknownClient"

    chart_data = None; final_report_content = None; svg_filepath_actual = None; modified_svg_filepath_actual = None; chart_image_path_png_actual = None; main_pdf_created = False; overall_success = False; sections_with_errors = None

    try:
        # Step 1: Calculate Chart
        logger.info("[Step 1/6] Calculating birth chart...")
        if not ephe_path and swe: logger.warning("Ephemeris path not set, calculation might use default or fail.")
        effective_full_name = full_name if full_name else client_name
        # Ensure gender is passed, required by calculate_chart signature
        gender_for_calc = gender if gender else "Unknown" # Pass a default if None
        chart_data = calculate_chart( **birth_info_for_calc, gender=gender_for_calc, full_name=effective_full_name, ephemeris_path_used=ephe_path )
        if not isinstance(chart_data, dict) or "error" in chart_data:
            logger.critical(f"Chart calculation failed: {chart_data.get('error', 'Unknown')}")
            return # Use return instead of raise to allow finally block
        logger.info("       -> Chart calculation successful.")

        # Step 2 & 3: Generate Chart Images
        logger.info("[Step 2&3/6] Generating Chart Images (Optional)...")
        if _kerykeion_available and KerykeionClass and ChartMakerClass:
            try:
                 year = birth_info_for_calc.get('year')
                 month = birth_info_for_calc.get('month')
                 day = birth_info_for_calc.get('day')
                 hour = birth_info_for_calc.get('hour')
                 minute = birth_info_for_calc.get('minute')
                 city = birth_info_for_calc.get('city')
                 country = birth_info_for_calc.get('country')
                 lng = birth_info_for_calc.get('lng')
                 lat = birth_info_for_calc.get('lat')
                 tz_str = birth_info_for_calc.get('tz_str')
                 if None in [year, month, day, hour, minute, city, country, lng, lat, tz_str]:
                     logger.warning("Skipping Kerykeion chart generation: Essential birth info missing.")
                 else:
                     year, month, day, hour, minute = map(int, (year, month, day, hour, minute))
                     lng, lat = float(lng), float(lat)
                     k_instance = KerykeionClass(safe_client_name, year, month, day, hour, minute, city, country, lng=lng, lat=lat, tz_str=tz_str)
                     temp_dir = tempfile.gettempdir()
                     chart_maker = ChartMakerClass(first_obj=k_instance, chart_type='Natal', new_output_directory=temp_dir)
                     chart_maker.makeSVG()
                     kerykeion_generated_filename = f"{safe_client_name} - Natal Chart.svg"
                     svg_filepath_actual = os.path.join(temp_dir, kerykeion_generated_filename)
                     if os.path.exists(svg_filepath_actual):
                         logger.info(f"       -> Kerykeion SVG created (temp): {svg_filepath_actual}")
                         try:
                             with open(svg_filepath_actual, 'r', encoding='utf-8') as f_in: original_svg_content = f_in.read()
                             processed_svg_content = replace_css_variables(original_svg_content)
                             modified_svg_filepath_actual = svg_filepath_actual
                             with open(modified_svg_filepath_actual, 'w', encoding='utf-8') as f_out: f_out.write(processed_svg_content)
                             logger.info(f"       -> Processed SVG saved over temp: {modified_svg_filepath_actual}")
                         except Exception as css_err:
                             logger.error(f"Error processing CSS vars in SVG: {css_err}", exc_info=True)
                             modified_svg_filepath_actual = svg_filepath_actual
                         if modified_svg_filepath_actual and _cairosvg_available:
                             try:
                                 logger.info(f"       -> Converting SVG to PNG...")
                                 png_output_dir = os.path.dirname(output_path)
                                 os.makedirs(png_output_dir, exist_ok=True)
                                 timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                 report_type_abbr = "Pet" if is_pet_report else "Human"
                                 occasion_abbr = "".join(c for c in occasion_mode.lower() if c.isalnum() or c == '_').replace("_", "")[:15] or "Default"
                                 breed_abbr = f"_{''.join(c for c in pet_breed if c.isalnum()).lower()[:8]}" if is_pet_report and pet_breed else ""
                                 chart_image_filename_png = f"chart_wheel_{safe_client_name}_{report_type_abbr}{breed_abbr}_{occasion_abbr}_{timestamp}.png"
                                 chart_image_path_png = os.path.join(png_output_dir, chart_image_filename_png)
                                 cairosvg.svg2png( url=modified_svg_filepath_actual, write_to=chart_image_path_png, scale=1.5, background_color="white" )
                                 if os.path.exists(chart_image_path_png) and os.path.getsize(chart_image_path_png) > 100:
                                     chart_image_path_png_actual = chart_image_path_png
                                     logger.info(f"       -> Chart PNG generated: {chart_image_path_png_actual}")
                                 else: logger.warning(f"CairoSVG PNG generation failed or file empty: {chart_image_path_png}")
                             except Exception as conversion_err: logger.error(f"CairoSVG conversion error: {conversion_err}", exc_info=True)
                         elif not _cairosvg_available: logger.info("       -> Skipping PNG generation: CairoSVG unavailable.")
                     else: logger.error(f"Kerykeion SVG failed, file not found: {svg_filepath_actual}")
            except Exception as svg_err: logger.error(f"Kerykeion chart generation error: {svg_err}", exc_info=True)
        else: logger.info("       -> Skipping SVG/PNG chart generation (Kerykeion unavailable).")

        # Step 4: Generate AI Content
        logger.info("[Step 4/6] Generating report content via AI...")
        if not TEST_MODE and not client: raise RuntimeError("OpenAI client not available for live AI call.")
        final_report_content = generate_report_content_via_ai( # Calls the corrected function
            chart_data=chart_data, client_name=client_name, gender=gender,
            client_instance=client, test_mode_flag=TEST_MODE, prompts_list=PROMPTS_TO_USE,
            occasion_mode=occasion_mode, is_pet_report=is_pet_report,
            pet_breed=pet_breed, pet_species=pet_species
        )
        # ... (error checking for final_report_content)
        if not isinstance(final_report_content, dict) or "error" in final_report_content:
             logger.critical(f"Content generation failed: {final_report_content.get('error', 'Unknown')}")
             return
        sections_with_errors = {k: v for k, v in final_report_content.items() if v.get('error_flag')}
        if sections_with_errors:
            logger.warning(f"       -> AI content generation completed with errors in {len(sections_with_errors)} sections.")
            for skey in sections_with_errors.keys(): logger.warning(f"         - Section {skey} flagged with error.")
        else: logger.info("       -> AI content generation loop completed successfully for all sections.")


        # Step 5: Validating Content (Placeholder)
        logger.info("[Step 5/6] Validating generated content structure (Placeholder)...")
        validation_passed, issue_count = validate_generated_content(final_report_content)
        if not validation_passed or issue_count > 0:
            logger.warning(f"       -> Placeholder content validation found {issue_count} potential issues. Review PDF carefully.")
        else: logger.info("       -> Placeholder content structure validation passed.")

        # Step 6: Generate PDF
        logger.info("[Step 6/6] Generating Main Report PDF...")
        # This 'main' function is assumed to be for HUMAN reports based on its filename/context
        if not is_pet_report:
            # --- Prepare context/data specifically for generate_human_pdf ---
            # Convert final_report_content dict to list ordered by PROMPTS_TO_USE
            sections_list_for_human_pdf = []
            if isinstance(PROMPTS_TO_USE, list) and isinstance(final_report_content, dict):
                for prompt_def in PROMPTS_TO_USE:
                    section_id = prompt_def.get("section_id")
                    if section_id and section_id in final_report_content:
                        pdf_section_data = {
                            'header': final_report_content[section_id].get('header', prompt_def.get('header', section_id)),
                            'ai_content': final_report_content[section_id].get('ai_generated_content', ''),
                            'quote': final_report_content[section_id].get('quote', prompt_def.get('quote'))
                        }
                        sections_list_for_human_pdf.append(pdf_section_data)
                    elif section_id:
                        logger.warning(f"Section {section_id} defined in PROMPTS but not found in final_report_content for PDF.")

            # Define paths needed by generate_human_pdf
            current_script_dir_for_paths = os.path.dirname(os.path.abspath(__file__)) # human_report/
            assets_dir_for_human_pdf = os.path.join(current_script_dir_for_paths, 'assets') # Assumes human_report/assets
            fonts_dir_for_human_pdf = os.path.join(current_script_dir_for_paths, 'fonts') # Assumes human_report/fonts
            # Data JSON dir should be the common one
            data_jsons_dir_for_human_pdf = COMMON_DATA_JSON_DIR # Imported from common.json_loader

            if not data_jsons_dir_for_human_pdf:
                 logger.error("COMMON_DATA_JSON_DIR is not set, cannot provide data path to human PDF generator.")
                 return # Stop if common data path is missing

            # Call the imported human PDF generator function
            logger.info(f"Calling generate_human_pdf for client: {client_name}")
            main_pdf_created = generate_human_pdf(
                 output_path=output_path, # Use the path passed into this main orchestrator function
                 client_name=client_name,
                 sections_data=sections_list_for_human_pdf, # Pass the formatted list
                 occasion_style_key=occasion_mode,
                 assets_base_dir=assets_dir_for_human_pdf,
                 fonts_base_dir=fonts_dir_for_human_pdf,
                 data_jsons_dir=data_jsons_dir_for_human_pdf # Pass the common data dir path
            )
            if main_pdf_created:
                overall_success = True
                logger.info(f"       -> Main Human Report PDF generated successfully: {output_path}")
            else:
                overall_success = False
                logger.error("       -> Main Human Report PDF generation FAILED.")
        else:
             # If this orchestrator is accidentally called for a pet report, log it.
             logger.warning("This orchestrator (generate_advanced_astrology_report.py) is intended for HUMAN reports. Skipping PDF generation for pet report.")
             overall_success = True # Consider it "successful" in terms of this script's scope (it calculated data)

    # --- Error Handling ---
    except (FileNotFoundError, ImportError, AuthenticationError, OpenAIError, RuntimeError, ValueError, TypeError) as critical_err:
        logger.critical(f"WORKFLOW HALTED by critical error: {type(critical_err).__name__}: {critical_err}", exc_info=True)
        overall_success = False
    except Exception as e: # Catch any other unexpected exceptions
        logger.critical(f"UNEXPECTED WORKFLOW ERROR: {type(e).__name__}: {e}", exc_info=True)
        overall_success = False
    # --- Cleanup ---
    finally:
        logger.info("\n--- File Generation Status & Cleanup ---")
        # Use .get() safely in case variables weren't assigned due to early errors
        kerykeion_svg_path = locals().get('svg_filepath_actual', "N/A")
        png_path = locals().get('chart_image_path_png_actual', "N/A")
        # Use the output_path parameter passed into main for the final PDF path check
        final_pdf_path_check = locals().get('output_path', "N/A")

        logger.info(f"Temp Kerykeion SVG Path: {kerykeion_svg_path}")
        logger.info(f"Final Chart PNG Path: {png_path}")
        if overall_success and final_pdf_path_check != "N/A" and os.path.exists(final_pdf_path_check):
            logger.info(f"       ✅ Final Report PDF generated successfully: {final_pdf_path_check}")
            logger.info("Attempting cleanup of intermediate image files...")
            # Only clean up the SVG file from the temp directory
            # Ensure the path is a string and not the default "N/A"
            files_to_clean = [p for p in [kerykeion_svg_path] if isinstance(p, str) and p != "N/A"]
            cleaned_count = 0
            for file_path in files_to_clean:
                try:
                    if os.path.exists(file_path):
                        # Extra check to ensure it's in the temp directory
                        # Compare absolute paths to be safe
                        if os.path.dirname(os.path.abspath(file_path)) == os.path.abspath(tempfile.gettempdir()):
                            os.remove(file_path)
                            logger.info(f"         - Removed temp file: {os.path.basename(file_path)}")
                            cleaned_count += 1
                        else: logger.warning(f"Skipping cleanup of file not in temp dir: {file_path}")
                    else: logger.debug(f"Temp file already removed or not created: {file_path}")
                except OSError as clean_err: logger.warning(f"         - Failed to remove {os.path.basename(file_path)}: {clean_err}")
            logger.info(f"Cleanup finished. Removed {cleaned_count} temp files.")
        elif not is_pet_report: # Only log failure if it was supposed to be a human report
            logger.error(f"       ❌ Report generation FAILED.")
            # Provide more specific feedback based on where it likely failed
            if 'chart_data' not in locals() or not isinstance(chart_data, dict) or ("error" in chart_data and chart_data.get('error') != 'Unknown'): logger.error("                 - Failure likely during chart calculation.")
            elif 'final_report_content' not in locals() or not isinstance(final_report_content, dict): logger.error("                 - Failure likely during AI content generation (result is not a dict).")
            elif sections_with_errors: logger.error(f"                 - Failure in AI generation (errors in {len(sections_with_errors)} sections) or subsequent step.")
            elif not main_pdf_created and 'pdf_generation_context' in locals(): logger.error("                 - Failure likely during PDF generation.")
            else: logger.error("                 - Unspecified failure.")
            logger.warning("       Temporary files (like SVG/PNG) may NOT have been cleaned up.")
            logger.info(f"       ℹ️ Final PDF path (may be incomplete/missing): {final_pdf_path_check}")
        else: # Pet report case handled by run_pet_report.py
             logger.info("       -> Human orchestrator finished (Pet report PDF generated by pet_report/run_pet_report.py).")


        end_time = datetime.now()
        start_time_local = locals().get('start_time', end_time) # Safely get start_time
        logger.info(f"\n🏁 Finished in: {end_time - start_time_local}")


# === Script Execution Guard ===
# ... (Full __main__ block from previous version) ...
if __name__ == "__main__":
    # Set logger level for __main__ execution
    # Get the main logger instance defined globally
    # The level is already set by the env var/arg parsing logic above the main function definition

    if '__version__' not in locals():
        __version__ = "Unknown (Direct Run)"
    # --- Argparse Setup ---
    parser = argparse.ArgumentParser(description=f"Generate Advanced Astrology Report (V{__version__})")
    # Arguments for birth info
    # Make year, month, day, hour, minute, lat, lng optional if --pet is used
    parser.add_argument("--year", type=int, required=False, help="Birth year (YYYY)")
    parser.add_argument("--month", type=int, required=False, help="Birth month (1-12)")
    parser.add_argument("--day", type=int, required=False, help="Birth day (1-31)")
    parser.add_argument("--hour", type=int, required=False, help="Birth hour (0-23, local time). Defaults to 12 in pet mode if not provided.")
    parser.add_argument("--minute", type=int, required=False, help="Birth minute (0-59, local time). Defaults to 0 in pet mode if not provided.")
    parser.add_argument("--lat", type=float, required=False, help="Birth latitude (decimal degrees)")
    parser.add_argument("--lng", type=float, required=False, help="Birth longitude (decimal degrees)")
    # Keep city, country, tz_str required as they are needed for location even in pet mode
    parser.add_argument("--city", type=str, required=True, help="Birth city")
    parser.add_argument("--country", type=str, required=True, help="Birth country")
    parser.add_argument("--tz_str", type=str, required=True, help="Timezone string (e.g., America/New_York)")
    # Arguments for client info and report type
    parser.add_argument("--name", type=str, required=True, help="Client's first name (or Pet's name)")
    parser.add_argument("--gender", type=str, default="Prefer not to say", help="Client gender") # Keep gender for human reports or potential pet context
    parser.add_argument("--full_name", type=str, default=None, help="Client's full name for numerology (optional)")
    parser.add_argument("--occasion", type=str, default="default", help="Occasion mode (e.g., birthday, self_discovery, pet_memorial, pet_birthday)") # Added pet occasions
    # Add --pet flag
    parser.add_argument("--pet", action='store_true', help="Generate a pet report instead of a human report.")
    parser.add_argument("--species", type=str, default="Animal", help="Pet species (e.g., Dog, Cat, Bird). Recommended if --pet is used.") # Added species, changed required text
    parser.add_argument("--breed", type=str, default=None, help="Pet breed (e.g., Golden Retriever, Siamese). Optional if --pet is used.") # Added breed
    # Optional arguments
    parser.add_argument("--house_system", type=str, default="P", choices=["P", "K", "R", "C", "E", "V"], help="House system code (Default: P - Placidus)")
    parser.add_argument("--log", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set console logging level")
    # Added output_path argument
    parser.add_argument("--output_path", type=str, default=None, help="Specify the output path for the PDF. Overrides default naming/location.")

    args = parser.parse_args()

    # --- Conditional Argument Validation and Defaulting ---
    # Check required arguments based on --pet flag
    if not args.pet:
        # If not a pet report, the standard birth chart arguments are required
        required_human_args = ['year', 'month', 'day', 'hour', 'minute', 'lat', 'lng']
        missing_human_args = [arg for arg in required_human_args if getattr(args, arg) is None]
        if missing_human_args:
            print(f"Error: The following arguments are required for human reports but were not provided: {', '.join(['--' + arg for arg in missing_human_args])}")
            parser.print_help()
            exit(1) # Exit if required human args are missing
    else:
        # If it is a pet report, apply defaults for optional birth time/location
        if args.hour is None:
            args.hour = 12
            logger.info("Pet report: Hour not provided, defaulting to 12.")
        if args.minute is None:
            args.minute = 0
            logger.info("Pet report: Minute not provided, defaulting to 0.")
        # Note: year, month, day, lat, lng are optional in argparse but passed as None if not provided.
        # Default to today's date if no date is provided for a pet report.
        today = date.today()
        if args.year is None:
             args.year = today.year
             logger.info(f"Pet report: Year not provided, defaulting to current year ({args.year}).")
        if args.month is None:
             args.month = today.month
             logger.info(f"Pet report: Month not provided, defaulting to current month ({args.month}).")
        if args.day is None:
             args.day = today.day
             logger.info(f"Pet report: Day not provided, defaulting to current day ({args.day}).")


    # Construct the dictionary ONLY for parameters needed by calculate_chart
    birth_info_for_calc = {
        'year': args.year, 'month': args.month, 'day': args.day,
        'hour': args.hour, 'minute': args.minute, 'lat': args.lat, 'lng': args.lng,
        'city': args.city, 'country': args.country, 'tz_str': args.tz_str,
        'house_system': args.house_system.encode('utf-8'),
    }

    # Log a warning if --pet is used but --species is default or "Animal"
    if args.pet and args.species == "Animal":
        logger.warning("Pet report requested (--pet) but species is default 'Animal'. Consider providing --species.")
    # Log a warning if --pet is used but --breed is not provided
    if args.pet and not args.breed:
         logger.info("Pet report requested (--pet) but breed is not provided (--breed). Report may lack breed-specific nuance.")

    # Determine the final output path
    # If --output_path is provided, use it. Otherwise, use the default naming convention.
    if args.output_path:
        final_pdf_path_to_use = args.output_path
        # Ensure the directory for the specified output path exists
        output_dir_specified = os.path.dirname(final_pdf_path_to_use)
        if output_dir_specified and not os.path.exists(output_dir_specified):
            try:
                os.makedirs(output_dir_specified, exist_ok=True)
                logger.info(f"Ensured output directory for specified path: {output_dir_specified}")
            except OSError as e:
                logger.critical(f"Could not create directory for specified output path: {output_dir_specified}. Error: {e}")
                raise # Stop if output dir cannot be created
    else:
        # Use the default naming convention determined earlier
        # This logic needs to be moved down or re-evaluated after argparse
        # Let's regenerate the default path here using the (potentially defaulted) args
        safe_client_name = "".join(c for c in args.name if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_") or "UnknownClient"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') # Use current time for filename
        report_type_abbr = "Pet" if args.pet else "Human"
        occasion_abbr = "".join(c for c in args.occasion.lower() if c.isalnum() or c == '_').replace("_", "")[:15] or "Default"
        breed_abbr = f"_{''.join(c for c in args.breed if c.isalnum()).lower()[:8]}" if args.pet and args.breed else ""
        final_pdf_filename = f"Cosmic_Blueprint_{safe_client_name}_{report_type_abbr}{breed_abbr}_{occasion_abbr}_{timestamp}.pdf"
        final_pdf_path_to_use = os.path.join(PDF_OUTPUT_DIR, final_pdf_filename)

    logger.info(f"Final output PDF path determined: {final_pdf_path_to_use}")


    # Validate Occasion Mode using the globally loaded styles from this orchestrator script
    default_occasion = "pet_default" if args.pet else "human_default" # Use args.pet directly here
    # available_occasions are the keys from the loaded JSON
    available_occasions = list(OCCASION_STYLES_FROM_ORCHESTRATOR.keys())

    # Determine the final occasion mode to use
    final_occasion_mode = args.occasion.lower() # Start with the user input
    if final_occasion_mode == "default":
        final_occasion_mode = default_occasion # Correctly assign the inferred default
        logger.info(f"Occasion mode 'default' specified, using inferred default: '{final_occasion_mode}'")
    elif final_occasion_mode not in available_occasions:
        logger.warning(f"Occasion '{final_occasion_mode}' not defined in occasion_styles.json—using default styling based on report type.")
        # If an invalid occasion is provided, fall back to the *report type's default* occasion for styling/logic,
        # but potentially keep the user's invalid occasion string in the filename for traceability if desired.
        # Let's use the *default* occasion for the actual report logic flow to ensure it runs.
        final_occasion_mode = default_occasion # Use the determined default occasion for logic
        # Note: The filename will still use the original 'occasion_abbr' which might reflect the user's input.

    else:
        # final_occasion_mode is already set to the valid occasion_mode here from args.occasion
        logger.info(f"Using validated occasion mode: '{final_occasion_mode}'")

    # Log Startup Info
    logger.info("-" * 60)
    # Corrected logger call to use args.name
    logger.info(f"Starting Report Generation (Orchestrator V{__version__}) for: {args.name}")
    logger.info(f"Report Type: {'Pet' if args.pet else 'Human'} | Occasion: {final_occasion_mode}")
    if args.pet:
        logger.info(f"Species: {args.species}, Breed: {args.breed if args.breed else 'N/A'}")
    # Log output and AI settings
    logger.info(f"Output Dir: {PDF_OUTPUT_DIR}")
    logger.info(f"Final Output Path: {final_pdf_path_to_use}")
    logger.info(f"Test Mode (AI): {TEST_MODE}")
    if not TEST_MODE:
        logger.info(f"AI Model: {AI_MODEL}, Temp: {AI_TEMPERATURE}")
    logger.info("-" * 60)

    # Execute Main Workflow
    # Pass the final_occasion_mode and pet_breed determined by the validation logic/args
    try:
        main(
            birth_info_for_calc=birth_info_for_calc, # Pass the dictionary for calculation
            client_name=args.name, # Pass args.name as client_name to the main function
            gender=args.gender, # Pass args.gender
            occasion_mode=final_occasion_mode, # Pass the *validated/defaulted* occasion mode
            full_name=args.full_name if args.full_name else args.name, # Pass args.full_name or args.name
            is_pet_report=args.pet, # Pass args.pet directly here
            pet_breed=args.breed, # Pass the explicit pet_breed argument
            pet_species=args.species, # Pass the explicit pet_species argument
            output_path=final_pdf_path_to_use # Pass the determined final output path
        )
    except Exception as main_err:
        logger.critical(f"Error during main workflow execution: {main_err}", exc_info=True)
    logger.info("--- Script Execution Complete ---")

# END OF FILE generate_advanced_astrology_report.py