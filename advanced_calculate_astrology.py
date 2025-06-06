# advanced_calculate_astrology.py
# --- Refactored ALL inline control flow statements to standard blocks ---
# --- VERSION 7.42.0: Refined zoneinfo time conversion logic ---
# --- VERSION 7.41.0: Added Midpoints, Dignities, True Node, Declinations & Aspects, Part of Spirit ---
# --- VERSION 7.40.13: Load Fixed Star data from external JSON ---
# --- VERSION 7.40.12: Integrated V2 Fixed Star calculation (incl. house pos & basic info) ---
# (Previous history...)
# --- VERSION 7.42.1: Corrected fixed star JSON filename reference ---
# --- VERSION 7.42.2 (Patched): Added explicit prompt-ready dominant/least elements ---
# --- VERSION 7.42.3: Ensure ephemeris_path_used is set at the start of calculate_chart ---
# --- VERSION 7.42.4 (PATCH): Corrected indentation for return statement in calculate_chart

import swisseph as swe
import os
from datetime import datetime, date, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from collections import Counter, defaultdict
import traceback
import json
import math
import logging
import re
from itertools import combinations
from dateutil.relativedelta import relativedelta


# Configure logger (Ensure it's configured before first use)
logger = logging.getLogger(__name__)
if not logger.handlers:
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - CALC - %(message)s')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)

# --- EPHEMERIS PATH AUTO-DETECT PATCH ---
try:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    ephe_dir_in_common = os.path.join(current_script_dir, "swisseph")
    if os.path.isdir(ephe_dir_in_common):
        swe.set_ephe_path(ephe_dir_in_common)
        logger.info(f"Swiss Ephemeris path set to: {ephe_dir_in_common}")
    else:
        logger.error(f"Swiss Ephemeris folder not found at expected path: {ephe_dir_in_common}")
except Exception as e:
    logger.error(f"Error setting Swiss Ephemeris path dynamically: {e}")



# --- Version ---
__version__ = "7.42.4" # Incremented for the fix

# --- Fixed Star Data and Configuration ---
try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
except NameError:
    script_dir = os.getcwd()
    logger.warning(f"__file__ not defined, using CWD for JSON data path: {script_dir}")

JSON_DATA_DIR = os.path.join(script_dir, "Data jsons")
logger.info(f"Expecting JSON data directory at: {JSON_DATA_DIR}")

FIXED_STAR_INFO = {}
FIXED_STAR_DATA_FILENAME = 'fixed_stars.json'
fixed_star_json_full_path = os.path.join(JSON_DATA_DIR, FIXED_STAR_DATA_FILENAME)

try:
    logger.info(f"Attempting to load fixed star data from: {fixed_star_json_full_path}")
    if not os.path.exists(fixed_star_json_full_path):
        project_root_guess = os.path.dirname(script_dir)
        alt_json_data_dir_common = os.path.join(project_root_guess, "common", "Data jsons")
        alt_json_data_dir_root = os.path.join(project_root_guess, "Data jsons")

        if os.path.exists(os.path.join(alt_json_data_dir_common, FIXED_STAR_DATA_FILENAME)):
            fixed_star_json_full_path = os.path.join(alt_json_data_dir_common, FIXED_STAR_DATA_FILENAME)
            logger.info(f"Found fixed star data at alternative common path: {fixed_star_json_full_path}")
        elif os.path.exists(os.path.join(alt_json_data_dir_root, FIXED_STAR_DATA_FILENAME)):
            fixed_star_json_full_path = os.path.join(alt_json_data_dir_root, FIXED_STAR_DATA_FILENAME)
            logger.info(f"Found fixed star data at alternative root path: {fixed_star_json_full_path}")
        else:
            raise FileNotFoundError(f"Fixed star JSON file not found at primary path: {os.path.join(JSON_DATA_DIR, FIXED_STAR_DATA_FILENAME)} or common alternatives.")


    with open(fixed_star_json_full_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
        FIXED_STAR_INFO = loaded_data.get("fixed_stars", {})
        if not FIXED_STAR_INFO:
            logger.warning(f"'{FIXED_STAR_DATA_FILENAME}' loaded but 'fixed_stars' key missing or empty inside JSON.")

    if FIXED_STAR_INFO:
        logger.info(f"Successfully loaded data for {len(FIXED_STAR_INFO)} fixed stars from '{FIXED_STAR_DATA_FILENAME}'.")
    else:
        logger.warning(f"No fixed star data loaded into FIXED_STAR_INFO from '{FIXED_STAR_DATA_FILENAME}'.")

except FileNotFoundError as fnf_err:
    logger.error(f"ERROR: {fnf_err}")
except json.JSONDecodeError:
    logger.error(f"ERROR: Could not decode JSON from '{fixed_star_json_full_path}'. Check the file for syntax errors.")
except Exception as e:
    logger.error(f"ERROR: An unexpected error occurred loading fixed star data: {e}")

DEFAULT_FIXED_STAR_NAMES = tuple(FIXED_STAR_INFO.keys()) if FIXED_STAR_INFO else ()
FIXED_STAR_ORB = 2.0


# Optional Imports
def fallback_calculate_ley_lines(lat, lng, loc_str):
    logger.warning("Using fallback calculate_ley_lines")
    return []
try:
    from leyline_calculations import calculate_ley_lines
    logger.info("Ley line module found.")
except ImportError:
    logger.warning("leyline_calculations.py not found...")
    calculate_ley_lines = fallback_calculate_ley_lines

def fallback_get_schumann_resonance():
    logger.warning("Using fallback get_schumann_resonance")
    return {"frequency": 7.83, "source": "default_module_missing"}
try:
    from schumann_api import get_schumann_resonance
    logger.info("Schumann API module found.")
except ImportError:
    logger.warning("schumann_api.py not found...")
    get_schumann_resonance = fallback_get_schumann_resonance
try:
    from geopy.geocoders import Nominatim
    _geopy_available = True
    logger.info("Geopy library found.")
except ImportError:
    logger.warning("geopy library not found.")
    _geopy_available = False


# --- Astrological Maps & Constants ---
ELEMENT_MAP = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}
TRADITIONAL_RULER_MAP = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter"
}
MODALITY_MAP = {
    "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
    "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable"
}
POINTS_FOR_BALANCE = [
    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus',
    'Neptune', 'Pluto', #'North Node', 'South Node', # Nodes often excluded
    'Ascendant', 'Midheaven'
]
ASPECT_DEFINITIONS = {
    "Conjunction": {"angle": 0.0, "type": "major"}, "Opposition": {"angle": 180.0, "type": "major"},
    "Square": {"angle": 90.0, "type": "major"}, "Trine": {"angle": 120.0, "type": "major"},
    "Sextile": {"angle": 60.0, "type": "major"},
    "Quincunx": {"angle": 150.0, "type": "minor"},
    "SemiSextile": {"angle": 30.0, "type": "minor"},
    "SemiSquare": {"angle": 45.0, "type": "minor"},
    "SesquiQuadrate": {"angle": 135.0, "type": "minor"},
    "Quintile": {"angle": 72.0, "type": "minor"},
    "BiQuintile": {"angle": 144.0, "type": "minor"},
}
ORB_SETTINGS = {
    "major": {
        "Conjunction": {"luminary": 10.0, "default": 8.0},
        "Opposition": {"luminary": 10.0, "default": 8.0},
        "Square": {"luminary": 8.0, "default": 7.0},
        "Trine": {"luminary": 8.0, "default": 7.0},
        "Sextile": {"luminary": 7.0, "default": 6.0},
        "default_orb": {"luminary": 8.0, "default": 7.0}
    },
    "minor": {
        "Quincunx": {"luminary": 3.0, "default": 2.5},
        "SemiSextile": {"luminary": 2.0, "default": 1.5},
        "SemiSquare": {"luminary": 2.5, "default": 2.0},
        "SesquiQuadrate": {"luminary": 2.5, "default": 2.0},
        "Quintile": {"luminary": 2.0, "default": 1.5},
        "BiQuintile": {"luminary": 2.0, "default": 1.5},
        "default_orb": {"luminary": 2.0, "default": 1.5}
    },
}
ASPECT_POINTS_FROM = [
    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
    'Uranus', 'Neptune', 'Pluto', 'Chiron', 'North Node', 'True Node',
    'Ascendant', 'Midheaven'
]
ASPECT_POINTS_TO = [
    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
    'Uranus', 'Neptune', 'Pluto', 'Chiron', 'North Node', 'South Node', 'True Node',
    'Ascendant', 'Midheaven', 'IC', 'DC',
    'Ceres', 'Pallas', 'Juno', 'Vesta',
    'Part of Fortune', 'Part of Spirit'
]
MAJOR_TRANSIT_ASPECTS = {
    "Conjunction": {"angle": 0.0},
    "Opposition":  {"angle": 180.0},
    "Square":      {"angle": 90.0},
    "Trine":       {"angle": 120.0},
}
OUTER_TRANSIT_PLANETS = {
    "Saturn":  swe.SATURN,
    "Uranus":  swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto":   swe.PLUTO,
    "Chiron":  swe.CHIRON,
}
ESSENTIAL_DIGNITY_RULES = {
    "Sun":     {"Aries": "Exaltation", "Leo": "Rulership", "Libra": "Fall", "Aquarius": "Detriment"},
    "Moon":    {"Taurus": "Exaltation", "Cancer": "Rulership", "Scorpio": "Fall", "Capricorn": "Detriment"},
    "Mercury": {"Gemini": "Rulership", "Virgo": "Rulership", "Virgo": "Exaltation", # Virgo is both Rulership and Exaltation
                "Sagittarius": "Detriment", "Pisces": "Detriment", "Pisces": "Fall"}, # Pisces is both Detriment and Fall
    "Venus":   {"Taurus": "Rulership", "Libra": "Rulership", "Pisces": "Exaltation",
                "Scorpio": "Detriment", "Aries": "Detriment", "Virgo": "Fall"},
    "Mars":    {"Aries": "Rulership", "Scorpio": "Rulership", "Capricorn": "Exaltation",
                "Libra": "Detriment", "Taurus": "Detriment", "Cancer": "Fall"},
    "Jupiter": {"Sagittarius": "Rulership", "Pisces": "Rulership", "Cancer": "Exaltation",
                "Gemini": "Detriment", "Virgo": "Detriment", "Capricorn": "Fall"},
    "Saturn":  {"Capricorn": "Rulership", "Aquarius": "Rulership", "Libra": "Exaltation",
                "Cancer": "Detriment", "Leo": "Detriment", "Aries": "Fall"},
}
MIDPOINTS_TO_CALCULATE = [
    ('Sun', 'Moon'), ('Sun', 'Ascendant'), ('Sun', 'Midheaven'),
    ('Moon', 'Ascendant'), ('Moon', 'Midheaven'),
    ('Mercury', 'Venus'), ('Mercury', 'Mars'),
    ('Venus', 'Mars'), ('Venus', 'Jupiter'), ('Venus', 'Saturn'),
    ('Mars', 'Jupiter'), ('Mars', 'Saturn'),
    ('Jupiter', 'Saturn'), ('Jupiter', 'North Node'),
    ('Saturn', 'North Node'),
    ('Ascendant', 'Midheaven')
]
DECLINATION_POINTS = [
    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
    'Uranus', 'Neptune', 'Pluto', 'Chiron', 'North Node', 'True Node',
    'Ascendant', 'Midheaven'
]
DECLINATION_ORB = 1.0

def get_zodiac_sign(degree):
    try:
        degree_float = float(degree)
        degree_normalized = degree_float % 360.0
    except (ValueError, TypeError):
        logger.warning(f"Invalid degree '{degree}' for sign calculation.")
        return ("Error", 0.0) # Return a tuple for consistency
    
    if degree_normalized < 0: # Ensure positive degrees
        degree_normalized += 360.0

    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    # Epsilon for floating point comparisons, helps with edge cases like 29.99999 degrees
    epsilon = 1e-9 

    # Determine the sign index
    # If degree is very close to a cusp (e.g., 29.999999), floor might put it in the wrong sign
    # Subtracting epsilon before flooring for cusp degrees ensures it lands correctly.
    # However, for degrees like 0.000001, this could push it to the previous sign.
    # A more robust way for cusps is to handle them if they are exactly 0 after modulo.
    
    if abs(degree_normalized % 30.0) < epsilon and degree_normalized != 0.0: # Exactly on a cusp, but not 0 Aries
        sign_index = math.floor((degree_normalized - epsilon) / 30.0)
    else:
        sign_index = math.floor(degree_normalized / 30.0)

    if degree_normalized == 0.0: # Special case for 0 degrees Aries
        sign_index = 0
        
    sign_index = int(sign_index % 12) # Ensure it's within 0-11

    exact_degree = degree_normalized % 30.0
    
    # If exact_degree is extremely close to 30 (e.g., 29.9999999), it should be 0 of the next sign,
    # but the sign_index logic above should handle this. If it's 0.0000001, it's 0 of current sign.
    if abs(exact_degree - 30.0) < epsilon: # Should not happen if sign_index is correct
        exact_degree = 0.0
    elif abs(exact_degree) < epsilon: # Handle exact 0 degree of a sign
        exact_degree = 0.0

    if 0 <= sign_index < 12:
        return (signs[sign_index], round(exact_degree, 4))
    else:
        # This case should ideally not be reached if logic is sound
        logger.error(f"Zodiac sign index {sign_index} out of range: deg={degree_normalized:.4f}")
        return ("Error", round(exact_degree, 4))


def calculate_house(degree, house_cusps):
    logger.debug(f"Calculating house for degree: {degree}")
    if not isinstance(house_cusps, (list, tuple)) or len(house_cusps) < 12:
        logger.error(f"Invalid house_cusps provided (Type: {type(house_cusps)}, Length: {len(house_cusps) if isinstance(house_cusps, (list, tuple)) else 'N/A'}).")
        return 0 # Return 0 or raise error, indicating failure
    
    cusps_to_use = list(house_cusps[:12]) # Ensure we only use the first 12 if more are given

    try:
        degree_float = float(degree) % 360.0
        if degree_float < 0:
            degree_float += 360.0
    except (ValueError, TypeError):
        logger.warning(f"Invalid degree '{degree}' for house calculation.")
        return 0

    cusp_degrees_float = []
    for i, cusp in enumerate(cusps_to_use):
        try:
            if cusp is None: # Check for None explicitly
                raise ValueError(f"Cusp {i+1} is None")
            cusp_float = float(cusp) % 360.0
            if cusp_float < 0:
                cusp_float += 360.0
            cusp_degrees_float.append(cusp_float)
        except (ValueError, TypeError):
            logger.error(f"Invalid cusp value at index {i}: '{cusp}'.")
            return 0 # Indicate error
            
    if len(cusp_degrees_float) != 12: # Should have 12 valid cusps
        logger.error("Could not normalize all 12 cusps for house calculation.")
        return 0

    cusps_normalized = cusp_degrees_float
    logger.debug(f"  Normalized degree: {degree_float:.4f}")
    logger.debug(f"  Normalized cusps: {[f'{c:.4f}' for c in cusps_normalized]}")

    epsilon = 1e-9 # For floating point comparisons

    # Check if degree is exactly on a cusp
    for h in range(12):
        if abs(degree_float - cusps_normalized[h]) < epsilon:
            logger.debug(f"  -> Edge case: Degree {degree_float:.4f} on Cusp {h+1}. Assigning House {h+1}.")
            return h + 1 # Assign to the house it's the cusp of

    # Standard house placement logic
    for h in range(12):
        start_cusp = cusps_normalized[h]
        end_cusp = cusps_normalized[(h + 1) % 12] # Next cusp, wraps around for 12th house
        house_num = h + 1

        # Handle the case where house spans 0 degrees Aries (e.g., cusp 12 is 330°, cusp 1 is 30°)
        if start_cusp > end_cusp: # This house spans 0 degrees Aries
            # Degree is in this house if it's greater than start_cusp OR less than end_cusp
            if (degree_float >= start_cusp - epsilon) or (degree_float < end_cusp - epsilon):
                logger.debug(f"  -> Found in House {house_num} (spanning 0°): {start_cusp:.4f} <= {degree_float:.4f} or {degree_float:.4f} < {end_cusp:.4f}")
                return house_num
        else: # Normal case where start_cusp < end_cusp
            if (degree_float >= start_cusp - epsilon) and (degree_float < end_cusp - epsilon):
                logger.debug(f"  -> Found in House {house_num}: {start_cusp:.4f} <= {degree_float:.4f} < {end_cusp:.4f}")
                return house_num
                
    logger.warning(f"Could not place degree {degree_float:.4f} in any house. Cusps: {cusps_normalized}")
    return 0 # Default if not found (should ideally not happen with correct cusps)

def get_moon_phase_details(jd_ut, sun_deg, moon_deg):
    logger.debug("Calculating Moon Phase Details...")
    if sun_deg is None or moon_deg is None:
        logger.warning("Cannot calculate Moon phase: Sun or Moon degree is None.")
        return {"name": "Error", "percent_illuminated": 0.0, "angle": 0.0}
    try:
        angle = (float(moon_deg) - float(sun_deg)) % 360.0
        if angle < 0:
            angle += 360.0

        # Get illumination fraction from Swisseph
        flags = swe.FLG_SWIEPH # Use standard ephemeris flags
        pheno_result = swe.pheno_ut(jd_ut, swe.MOON, flags)
        
        if isinstance(pheno_result, tuple) and len(pheno_result) >= 2:
            illum_frac = pheno_result[1] # Illumination fraction is the second item
        else:
            logger.warning(f"swe.pheno_ut for Moon returned unexpected result: {pheno_result}")
            illum_frac = 0.0 # Default if result is not as expected

        illum_percent = round(illum_frac * 100.0, 1)
        phase_name = get_moon_phase_name(angle, illum_frac) # Pass illum_frac, not illum_percent
        logger.debug(f"  -> Moon Phase: Angle={angle:.2f}, Illum={illum_percent:.1f}%, Name={phase_name}")
        return {"name": phase_name, "percent_illuminated": illum_percent, "angle": round(angle, 2)}
    except Exception as e:
        logger.error(f"Error calculating Moon phase details: {e}", exc_info=True)
        return {"name": "Error", "percent_illuminated": 0.0, "angle": 0.0}


def get_moon_phase_name(phase_angle, illumination_fraction): # illumination_fraction is 0.0 to 1.0
    try:
        angle = float(phase_angle) % 360.0
        if angle < 0:
            angle += 360.0
        illum_percent = float(illumination_fraction) * 100.0
    except (ValueError, TypeError):
        logger.warning(f"Invalid moon phase input: Angle='{phase_angle}', IllumFraction='{illumination_fraction}'")
        return "Error"

    logger.debug(f"  Moon Phase Name Check: Angle={angle:.2f}°, Illum={illum_percent:.1f}%")

    # Determine phase name based on angle and illumination (more precise)
    if angle < 2.0 or angle >= 358.0: # New Moon (very small crescent or dark)
        phase_name = "New Moon"
    elif angle < 45.0: # Between New and First Quarter
        phase_name = "Waxing Crescent"
    elif angle < 88.0: # Approaching First Quarter
        phase_name = "First Quarter"
    elif angle < 135.0: # Between First Quarter and Full
        phase_name = "Waxing Gibbous"
    elif angle < 178.0: # Approaching Full Moon
        phase_name = "Full Moon"
    elif angle < 225.0: # After Full, before Last Quarter
        phase_name = "Waning Gibbous"
    elif angle < 268.0: # Approaching Last Quarter
        phase_name = "Last Quarter"
    elif angle < 315.0: # Between Last Quarter and New
        phase_name = "Waning Crescent"
    else: # Balsamic or very late Waning Crescent
        phase_name = "Balsamic Moon" # Or "Dark Moon" / "Waning Crescent"
    
    logger.debug(f"  -> Moon Phase Name Determined: {phase_name}")
    return phase_name

def sum_digits(n):
    s = 0
    try:
        # Handle potential float input, then convert to int, then to string
        num_str = str(int(float(n))) 
    except (ValueError, TypeError):
        logger.warning(f"Invalid input '{n}' for sum_digits.")
        return 0 # Return 0 for invalid input
        
    for digit in num_str:
        if digit.isdigit(): # Ensure it's a digit before converting
            s += int(digit)
    return s

def reduce_number(n):
    try:
        num = int(float(n)) # Allow float input, convert to int
    except (ValueError, TypeError):
        logger.warning(f"Invalid input '{n}' for reduce_number.")
        return 0 # Return 0 for invalid input

    if num < 0: # Work with absolute value for reduction
        num = abs(num)

    # Master numbers are not reduced further
    if num in [11, 22, 33]:
        return num
    
    while num > 9: # Reduce until single digit (or master number)
        num = sum_digits(num)
        if num in [11, 22, 33]: # Check for master number after each sum
            break
    return num

NUMEROLOGY_MAP_PYTHAGOREAN = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8,
}
VOWELS = "AEIOU" # Define vowels for Soul Urge

def _calculate_numerology_value(name, use_vowels_only=False):
    if not name or not isinstance(name, str):
        logger.debug("Numerology calculation skipped: Invalid name provided.")
        return 0
    total = 0
    # Clean name: remove non-alphabetic chars and convert to uppercase
    cleaned_name = re.sub(r'[^A-Z]', '', name.upper())
    if not cleaned_name:
        logger.debug("Numerology calculation skipped: Name contains no alphabetic characters after cleaning.")
        return 0

    target_letters = VOWELS if use_vowels_only else None
    
    for letter in cleaned_name:
        if target_letters and letter not in target_letters: # Skip if vowel-only and not a vowel
            continue
        value = NUMEROLOGY_MAP_PYTHAGOREAN.get(letter)
        if value is not None:
            total += value
        else:
            # This should not happen if cleaned_name only contains A-Z and map is complete
            logger.warning(f"Letter '{letter}' not found in Pythagorean map (Name: {name}, Cleaned: {cleaned_name})")
    return total

def _calculate_soul_urge(full_name):
    logger.debug(f"Calculating Soul Urge for: {full_name}")
    raw_sum = _calculate_numerology_value(full_name, use_vowels_only=True)
    reduced_num = reduce_number(raw_sum)
    logger.debug(f"  -> Raw Sum (Vowels): {raw_sum}, Reduced: {reduced_num}")
    return reduced_num

def _calculate_expression(full_name):
    logger.debug(f"Calculating Expression for: {full_name}")
    raw_sum = _calculate_numerology_value(full_name, use_vowels_only=False) # All letters
    reduced_num = reduce_number(raw_sum)
    logger.debug(f"  -> Raw Sum (All Letters): {raw_sum}, Reduced: {reduced_num}")
    return reduced_num

def get_essential_dignity(planet_name, sign):
    if planet_name not in ESSENTIAL_DIGNITY_RULES or sign == "Error": # Handle "Error" sign
        return "None"
    
    dignity_rules_for_planet = ESSENTIAL_DIGNITY_RULES[planet_name]
    dignity = dignity_rules_for_planet.get(sign, "None") # Default to "None" if sign not in planet's rules

    # Special handling for Mercury in Virgo/Pisces (both Rulership/Exaltation and Detriment/Fall)
    # The current ESSENTIAL_DIGNITY_RULES structure already prioritizes Rulership/Exaltation for Virgo,
    # and Detriment/Fall for Pisces due to dictionary key overwriting if listed multiple times.
    # If specific dual dignities need to be reported, the data structure or logic here would need adjustment.
    # For now, the existing logic should be fine for primary dignity.
    # Example: If Mercury is in Virgo, it's listed twice, rule for Exaltation might override Rulership.
    # Let's ensure Rulership takes precedence if both are possible for the same sign (e.g. Mercury in Virgo)
    if planet_name == "Mercury":
        if sign == "Virgo":
            # Virgo is both Rulership and Exaltation for Mercury. Often Rulership is primary.
            dignity = "Rulership" # Or prioritize based on specific astrological tradition
        elif sign == "Pisces":
            # Pisces is both Detriment and Fall for Mercury.
            dignity = "Detriment" # Or prioritize
            
    return dignity

def get_aspect_orb(p1_name, p2_name, aspect_name, aspect_type):
    is_luminary_involved = p1_name in ['Sun', 'Moon'] or p2_name in ['Sun', 'Moon']
    
    orb_type_settings = ORB_SETTINGS.get(aspect_type)
    if not orb_type_settings:
        logger.warning(f"No orb settings defined for aspect type '{aspect_type}'. Using fallback 1.0.")
        return 1.0 # Fallback orb

    aspect_specific_orbs = orb_type_settings.get(aspect_name)
    if not aspect_specific_orbs: # If aspect_name not in specific settings, use default for the type
        aspect_specific_orbs = orb_type_settings.get("default_orb")
        if not aspect_specific_orbs: # If no default_orb for the type, something is wrong with ORB_SETTINGS
            logger.warning(f"No orb settings for aspect '{aspect_name}' or default_orb for type '{aspect_type}'. Using fallback 1.0.")
            return 1.0 # Fallback orb
            
    if is_luminary_involved:
        return aspect_specific_orbs.get("luminary", aspect_specific_orbs.get("default", 1.0)) # Fallback to default if luminary not specified
    else:
        return aspect_specific_orbs.get("default", 1.0) # Fallback if default not specified (shouldn't happen with good ORB_SETTINGS)

def calculate_aspects(positions):
    logger.info("   Calculating Longitude Aspects...")
    aspects_found = defaultdict(list)
    processed_pairs = set() # To avoid duplicate aspects (e.g. Sun-Moon and Moon-Sun)

    if not positions:
        logger.warning("Aspect calculation skipped: Positions data is missing.")
        return aspects_found

    # Prepare a dictionary of valid points and their degrees for quick lookup
    point_degrees = {}
    all_aspect_points_set = set(ASPECT_POINTS_FROM) | set(ASPECT_POINTS_TO) # Combine all points considered for aspects
    for point_name in all_aspect_points_set:
        pos_data = positions.get(point_name)
        if isinstance(pos_data, dict) and pos_data.get('degree') is not None and pos_data.get('sign') != 'Error':
            try:
                point_degrees[point_name] = float(pos_data['degree'])
            except (ValueError, TypeError):
                logger.debug(f"Skipping {point_name} for aspects: invalid degree value '{pos_data.get('degree')}'.")
    
    valid_points_for_aspects = set(point_degrees.keys())
    logger.debug(f"         Valid points for aspect calculation: {valid_points_for_aspects}")

    # Iterate through combinations of points
    for p1_name in ASPECT_POINTS_FROM:
        if p1_name not in valid_points_for_aspects:
            continue
        p1_deg = point_degrees[p1_name]

        for p2_name in ASPECT_POINTS_TO:
            if p2_name not in valid_points_for_aspects or p1_name == p2_name: # No aspects to self
                continue
            
            pair = tuple(sorted((p1_name, p2_name))) # Canonical representation of the pair
            if pair in processed_pairs: # Already processed this pair
                continue
            
            p2_deg = point_degrees[p2_name]

            delta = abs(p1_deg - p2_deg)
            angular_distance = min(delta, 360.0 - delta) # Shortest arc

            best_match_for_pair = None
            min_orb_for_pair = 361.0 # Initialize with a value larger than any possible orb

            for aspect_name, aspect_info in ASPECT_DEFINITIONS.items():
                target_angle = aspect_info["angle"]
                aspect_type = aspect_info["type"] # "major" or "minor"
                
                orb_limit = get_aspect_orb(p1_name, p2_name, aspect_name, aspect_type)
                actual_orb = abs(angular_distance - target_angle)

                if actual_orb <= orb_limit:
                    # If this aspect is tighter than a previously found one for the same pair, replace it
                    if actual_orb < min_orb_for_pair:
                        min_orb_for_pair = actual_orb
                        best_match_for_pair = {
                            "planet1": p1_name, 
                            "planet2": p2_name, 
                            "aspect": aspect_name, 
                            "orb": round(actual_orb, 2),
                            "orb_limit": orb_limit,
                            "type": aspect_type
                        }
            
            if best_match_for_pair:
                aspects_found[p1_name].append(best_match_for_pair)
                # If p2_name is also in ASPECT_POINTS_FROM, add the reverse aspect for completeness if it's not the same point
                if p2_name in ASPECT_POINTS_FROM and p1_name != p2_name: 
                    aspect_detail_reverse = best_match_for_pair.copy()
                    aspect_detail_reverse["planet1"] = p2_name
                    aspect_detail_reverse["planet2"] = p1_name
                    aspects_found[p2_name].append(aspect_detail_reverse)
                
                logger.debug(f"            -> Aspect Added: {best_match_for_pair['planet1']} {best_match_for_pair['aspect']} {best_match_for_pair['planet2']} (Orb: {best_match_for_pair['orb']:.2f}°)")
                processed_pairs.add(pair) # Mark this pair as processed

    # Sort aspects for each planet by orb
    for planet_key in aspects_found:
        aspects_found[planet_key].sort(key=lambda x: x.get('orb', 99)) # Sort by orb, smallest first
        
    logger.info(f"   Longitude aspect calculation finished. Found aspects originating from {len(aspects_found)} points.")
    return dict(aspects_found) # Convert defaultdict to dict for final output

def detect_grand_trine(aspects, positions): # aspects is dict, positions is dict
    patterns = []
    trine_edges = set() # Store pairs of points that form a trine

    if not isinstance(aspects, dict):
        return patterns

    # Collect all trine edges
    for p, asp_list in aspects.items():
        if not isinstance(asp_list, list):
            continue
        for asp in asp_list:
            if isinstance(asp, dict) and asp.get('aspect') == 'Trine':
                q = asp.get('planet2')
                if p and q: # Ensure both points are valid
                    trine_edges.add(tuple(sorted([p, q]))) # Store as sorted tuple to avoid duplicates like (Sun,Moon) and (Moon,Sun)

    # Get list of points that have valid sign information for element check
    eligible_points = [p for p, data in positions.items() if isinstance(data, dict) and data.get('sign') not in [None, 'Error']]
    if len(eligible_points) < 3: # Need at least 3 points for a Grand Trine
        return patterns

    processed_combos = set() # To avoid duplicate Grand Trines if points are processed in different orders

    # Check all combinations of 3 eligible points
    for combo in combinations(eligible_points, 3):
        sorted_combo = tuple(sorted(combo)) # Canonical form for checking processed_combos
        if sorted_combo in processed_combos:
            continue

        p1, p2, p3 = combo
        
        # Check if all three pairs form trines
        pair1 = tuple(sorted([p1, p2]))
        pair2 = tuple(sorted([p1, p3]))
        pair3 = tuple(sorted([p2, p3]))

        if pair1 in trine_edges and pair2 in trine_edges and pair3 in trine_edges:
            # All three pairs are trines, now check if they are in the same element
            try:
                elems = [ELEMENT_MAP.get(positions[p]['sign']) for p in combo]
                if len(set(elems)) == 1 and elems[0] is not None: # All points in the same valid element
                    patterns.append({
                        'pattern': 'Grand Trine',
                        'points': list(combo), # Store as list for easier use later
                        'element': elems[0]
                    })
                    logger.debug(f"                      -> Detected Grand Trine: {sorted_combo} in {elems[0]}")
                    processed_combos.add(sorted_combo)
            except KeyError: # Should not happen if eligible_points logic is correct
                logger.warning(f"Could not check element for Grand Trine combo {combo} due to missing position data.")
                continue
            except TypeError: # If a sign or element is None unexpectedly
                logger.warning(f"Type error checking element for Grand Trine combo {combo}.")
                continue
    return patterns

def detect_t_square(aspects, orb=None): # Orb parameter currently not used, relies on aspects passed
    patterns = []
    if not isinstance(aspects, dict):
        return patterns

    oppositions = set()
    for p, asp_list in aspects.items():
        if not isinstance(asp_list, list): continue
        for asp in asp_list:
            if isinstance(asp, dict) and asp.get('aspect') == 'Opposition':
                q = asp.get('planet2')
                if p and q: oppositions.add(tuple(sorted([p, q])))
    
    if not oppositions: return patterns

    squares_map = defaultdict(set) # Maps a point to all points it squares
    for p, asp_list in aspects.items():
        if not isinstance(asp_list, list): continue
        for asp in asp_list:
            if isinstance(asp, dict) and asp.get('aspect') == 'Square':
                q = asp.get('planet2')
                if p and q:
                    squares_map[p].add(q)
                    squares_map[q].add(p) # Ensure symmetry

    processed_tsquares = set()
    for p1_opp, p2_opp in oppositions:
        # Find points that square both p1_opp and p2_opp
        common_apexes = squares_map[p1_opp].intersection(squares_map[p2_opp])
        for apex in common_apexes:
            if apex != p1_opp and apex != p2_opp: # Apex cannot be one of the opposition points
                t_square_points = tuple(sorted([p1_opp, p2_opp, apex]))
                if t_square_points not in processed_tsquares:
                    pattern_info = {'pattern': 'T-Square', 'points': list(t_square_points), 'apex': apex, 
                                    'opposition_pair': [p1_opp, p2_opp]}
                    patterns.append(pattern_info)
                    processed_tsquares.add(t_square_points)
                    logger.debug(f"                      -> Detected T-Square: Opposition={p1_opp}-{p2_opp}, Apex={apex}")
    return patterns


def detect_yod(aspects, orb=None): # Orb parameter currently not used
    patterns = []
    if not isinstance(aspects, dict): return patterns

    sextiles = set()
    for p, asp_list in aspects.items():
        if not isinstance(asp_list, list): continue
        for asp in asp_list:
            if isinstance(asp, dict) and asp.get('aspect') == 'Sextile':
                q = asp.get('planet2')
                if p and q: sextiles.add(tuple(sorted([p, q])))

    quincunxes_map = defaultdict(set) # Point -> set of points it quincunxes
    for p, asp_list in aspects.items():
        if not isinstance(asp_list, list): continue
        for asp in asp_list:
            if isinstance(asp, dict) and asp.get('aspect') == 'Quincunx':
                q = asp.get('planet2')
                if p and q:
                    quincunxes_map[p].add(q)
                    quincunxes_map[q].add(p)

    if not sextiles or not quincunxes_map: return patterns

    processed_yods = set()
    for p1_sext, p2_sext in sextiles:
        # Find points that quincunx both p1_sext and p2_sext
        common_apexes = quincunxes_map[p1_sext].intersection(quincunxes_map[p2_sext])
        for apex in common_apexes:
            if apex != p1_sext and apex != p2_sext:
                yod_points = tuple(sorted([p1_sext, p2_sext, apex]))
                if yod_points not in processed_yods:
                    pattern_info = {'pattern': 'Yod', 'points': list(yod_points), 'apex': apex,
                                    'sextile_pair': [p1_sext, p2_sext]}
                    patterns.append(pattern_info)
                    processed_yods.add(yod_points)
                    logger.debug(f"                      -> Detected Yod: Sextile={p1_sext}-{p2_sext}, Apex={apex}")
    return patterns


def detect_grand_cross(aspects, orb=None): # Orb parameter currently not used
    patterns = []
    if not isinstance(aspects, dict): return patterns

    oppositions_map = defaultdict(set)
    for p, asp_list in aspects.items():
        if not isinstance(asp_list, list): continue
        for asp in asp_list:
            if isinstance(asp, dict) and asp.get('aspect') == 'Opposition':
                q = asp.get('planet2')
                if p and q:
                    oppositions_map[p].add(q)
                    oppositions_map[q].add(p)
    
    squares_map = defaultdict(set)
    for p, asp_list in aspects.items():
        if not isinstance(asp_list, list): continue
        for asp in asp_list:
            if isinstance(asp, dict) and asp.get('aspect') == 'Square':
                q = asp.get('planet2')
                if p and q:
                    squares_map[p].add(q)
                    squares_map[q].add(p)

    if not oppositions_map or not squares_map: return patterns

    processed_crosses = set()
    all_points_in_oppositions = list(oppositions_map.keys())

    # Iterate through all combinations of 4 points
    for combo in combinations(all_points_in_oppositions, 4):
        p1, p2, p3, p4 = combo
        sorted_combo_tuple = tuple(sorted(combo))
        if sorted_combo_tuple in processed_crosses:
            continue

        # Check for two oppositions among these 4 points
        # (p1-p2 opp AND p3-p4 opp) OR (p1-p3 opp AND p2-p4 opp) OR (p1-p4 opp AND p2-p3 opp)
        opp_pair1, opp_pair2 = None, None
        if p2 in oppositions_map[p1] and p4 in oppositions_map[p3]:
            opp_pair1, opp_pair2 = (p1,p2), (p3,p4)
        elif p3 in oppositions_map[p1] and p4 in oppositions_map[p2]:
            opp_pair1, opp_pair2 = (p1,p3), (p2,p4)
        elif p4 in oppositions_map[p1] and p3 in oppositions_map[p2]:
            opp_pair1, opp_pair2 = (p1,p4), (p2,p3)
        
        if opp_pair1 and opp_pair2:
            # Now check if all 4 points square each other appropriately
            # Each point must square two others that are not its opposite.
            is_gc = True
            for point_in_cross in combo:
                other_points_in_opp_pair = list(set(opp_pair1) - {point_in_cross}) + list(set(opp_pair2) - {point_in_cross})
                # Remove duplicates if point_in_cross was part of both (not possible for GC)
                other_points_in_opp_pair = [op for op in other_points_in_opp_pair if op != point_in_cross]


                # Ensure it squares the two points that are NOT its direct opposite
                # Find its opposite
                opposite_point = None
                if point_in_cross == opp_pair1[0]: opposite_point = opp_pair1[1]
                elif point_in_cross == opp_pair1[1]: opposite_point = opp_pair1[0]
                elif point_in_cross == opp_pair2[0]: opposite_point = opp_pair2[1]
                elif point_in_cross == opp_pair2[1]: opposite_point = opp_pair2[0]

                if opposite_point is None: # Should not happen if logic is correct
                    is_gc = False; break 
                
                points_it_should_square = [p for p in combo if p != point_in_cross and p != opposite_point]
                
                if not (points_it_should_square[0] in squares_map[point_in_cross] and \
                        points_it_should_square[1] in squares_map[point_in_cross]):
                    is_gc = False
                    break
            
            if is_gc:
                patterns.append({'pattern': 'Grand Cross', 'points': list(sorted_combo_tuple)})
                processed_crosses.add(sorted_combo_tuple)
                logger.debug(f"                      -> Detected Grand Cross: {sorted_combo_tuple}")
    return patterns


def detect_stellium(positions, orb=10.0, min_planets=3): # Orb for conjunction-based stellium, sign/house is simpler
    patterns = []
    if not isinstance(positions, dict): return patterns

    # Points to consider for stellium (typically personal planets + relevant outers/points)
    points_to_consider = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'Ascendant', 'Midheaven', 'North Node']
    
    # Filter for points present in the chart with valid sign and degree
    points_for_stellium_data = []
    for p_name in points_to_consider:
        p_data = positions.get(p_name)
        if isinstance(p_data, dict) and p_data.get('sign') not in [None, 'Error'] and p_data.get('degree') is not None:
            points_for_stellium_data.append({'name': p_name, 'degree': p_data['degree'], 'sign': p_data['sign'], 'house': p_data.get('house')})

    if len(points_for_stellium_data) < min_planets:
        return patterns # Not enough points to form a stellium

    # Stellium by Sign
    sign_groups = defaultdict(list)
    for p_info in points_for_stellium_data:
        sign_groups[p_info['sign']].append(p_info['name'])

    for sign, plist in sign_groups.items():
        if len(plist) >= min_planets:
            patterns.append({'pattern': 'Stellium by Sign', 'points': sorted(plist), 'sign': sign})
            logger.debug(f"                      -> Detected Stellium by Sign: {sign} - {sorted(plist)}")

    # Stellium by House
    house_groups = defaultdict(list)
    for p_info in points_for_stellium_data:
        house = p_info.get('house')
        if house and house != 'Error' and house != 0: # Ensure house is valid and not 0
            try:
                house_int = int(house) # Make sure it's an int for grouping
                house_groups[house_int].append(p_info['name'])
            except (ValueError, TypeError):
                logger.debug(f"Could not use house '{house}' for stellium check for {p_info['name']}.")

    for house, plist in house_groups.items():
        if len(plist) >= min_planets:
            patterns.append({'pattern': 'Stellium by House', 'points': sorted(plist), 'house': house})
            logger.debug(f"                      -> Detected Stellium by House: House {house} - {sorted(plist)}")
    
    # Stellium by Conjunction (more complex, points close together regardless of sign/house boundaries)
    # This requires sorting points by degree and then iterating
    # Not implemented in this pass to keep it aligned with previous logic primarily focusing on sign/house.
    # If needed, this would involve sorting `points_for_stellium_data` by 'degree'
    # and then checking for clusters within the specified 'orb'.

    return patterns


def calculate_midpoint(deg1, deg2):
    try:
        d1 = float(deg1) % 360.0
        d2 = float(deg2) % 360.0
    except (TypeError, ValueError):
        logger.warning(f"Invalid input for midpoint calculation: {deg1}, {deg2}")
        return None

    # Calculate both short and long arc midpoints
    # Midpoint = (d1 + d2) / 2, then adjust for shortest arc
    # Alternative: Arc = abs(d1 - d2). If Arc > 180, use 360 - Arc. Midpoint = (d1 + Arc/2) % 360 or (d2 + Arc/2) % 360
    
    diff = abs(d1 - d2)
    arc_short = min(diff, 360.0 - diff) # Shortest arc between them
    
    # The midpoint will be along the shorter arc.
    # If (d1 + arc_short/2) % 360 is one midpoint, the other is ((d1 + arc_short/2) + 180) % 360
    # We need to determine which direction to add half_arc.
    
    half_arc = arc_short / 2.0
    
    # Test potential midpoints
    mid1 = (d1 + half_arc) % 360.0
    mid2 = (d1 - half_arc + 360.0) % 360.0 # Adding 360 ensures positive before modulo if d1 < half_arc

    # Check which one is closer to being equidistant or on the shorter path
    # A simpler way: if (d1 + arc_short) % 360 is "close" to d2, then d1 + half_arc is the correct direction
    # Or, if (d2 + arc_short) % 360 is "close" to d1
    
    # If d1 < d2:
    #   if d2 - d1 < 180 (shorter arc): midpoint = (d1 + d2) / 2
    #   else (longer arc chosen): midpoint = ((d1 + d2) / 2 + 180) % 360
    # If d1 > d2:
    #   if d1 - d2 < 180 (shorter arc): midpoint = (d1 + d2) / 2
    #   else (longer arc chosen): midpoint = ((d1 + d2) / 2 + 180) % 360
    
    # This can be simplified:
    midpoint_candidate = (d1 + d2) / 2.0
    if diff > 180.0: # If the direct sum went over the long arc
        midpoint_candidate = (midpoint_candidate + 180.0) % 360.0
        
    midpoint = midpoint_candidate % 360.0
    if midpoint < 0: midpoint += 360.0 # Ensure positive

    return midpoint

def calculate_declinations(jd_ut, bodies, positions): # bodies is name -> swe_id map
    logger.info("   Calculating Declinations...")
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED # FLG_SPEED not strictly needed for declination only, but often calc_ut is used for general pos
    
    for name, body_id in bodies.items():
        if name not in positions: # Skip if point not in main positions dict (e.g. if it's an angle handled separately)
            continue
        
        declination = None
        try:
            # For declination, we need equatorial coordinates.
            # swe.calc_ut with FLG_EQUATORIAL returns RA, Dec, Dist, SpeedRA, SpeedDec, SpeedDist
            calc_result_eq, ret_flag_eq = swe.calc_ut(jd_ut, body_id, swe.FLG_EQUATORIAL | swe.FLG_SWIEPH)
            
            if ret_flag_eq >= 0 and isinstance(calc_result_eq, (list, tuple)) and len(calc_result_eq) >= 2:
                # result[0] is Right Ascension, result[1] is Declination
                declination = calc_result_eq[1] 
                logger.debug(f"                    {name}: Dec={declination:.4f}")
            else:
                error_msg = f"Could not get equatorial coordinates for {name}. Flag: {ret_flag_eq}"
                if isinstance(calc_result_eq, str) : error_msg += f" Msg: {calc_result_eq}"
                logger.warning(error_msg)
        except Exception as e:
            logger.error(f"Error calculating declination for {name}: {e}", exc_info=False)

        if name in positions and isinstance(positions[name], dict):
            positions[name]['declination'] = declination
        elif name in positions: # Should not happen if positions[name] is always a dict
            logger.warning(f"Position entry for {name} is not a dict, cannot add declination.")

    # Calculate Declinations for Ascendant and Midheaven
    try:
        # ascmc_raw contains [asc, mc, armc, Gearth, vertex, equat_asc, coasc1, coasc2, polasc]
        # We need the ecliptic longitude of Asc and MC from ascmc_raw
        if 'ascmc_raw' in positions and isinstance(positions['ascmc_raw'], (list, tuple)) and len(positions['ascmc_raw']) >= 2:
            asc_lon_ecl = positions['ascmc_raw'][0] 
            mc_lon_ecl = positions['ascmc_raw'][1]
            
            # Get obliquity of ecliptic
            # swe.get_tid_acc returns [NutObl, TrueObl, MeanObl, NutLong, NutLat]
            eps_tuple = swe.get_tid_acc(jd_ut, swe.FLG_SWIEPH) # Use current JD
            true_obliquity = eps_tuple[1] # True obliquity of the ecliptic

            # Ascendant Declination: sin(Dec) = sin(Eps) * sin(Lambda_Asc)
            try:
                asc_lon_rad = math.radians(asc_lon_ecl)
                eps_rad = math.radians(true_obliquity)
                asc_dec_rad = math.asin(math.sin(eps_rad) * math.sin(asc_lon_rad))
                asc_declination = math.degrees(asc_dec_rad)
                if 'Ascendant' in positions and isinstance(positions['Ascendant'], dict):
                    positions['Ascendant']['declination'] = asc_declination
                logger.debug(f"                    Ascendant: EclLon={asc_lon_ecl:.4f}, TrueObl={true_obliquity:.4f} -> Dec={asc_declination:.4f}")
            except Exception as asc_dec_err:
                logger.error(f"Error calculating Ascendant declination: {asc_dec_err}")
                if 'Ascendant' in positions and isinstance(positions['Ascendant'], dict): positions['Ascendant']['declination'] = None
            
            # Midheaven Declination: sin(Dec) = sin(Eps) * sin(Lambda_MC)
            try:
                mc_lon_rad = math.radians(mc_lon_ecl)
                # eps_rad is already calculated
                mc_dec_rad = math.asin(math.sin(eps_rad) * math.sin(mc_lon_rad))
                mc_declination = math.degrees(mc_dec_rad)
                if 'Midheaven' in positions and isinstance(positions['Midheaven'], dict):
                    positions['Midheaven']['declination'] = mc_declination
                logger.debug(f"                    Midheaven: EclLon={mc_lon_ecl:.4f}, TrueObl={true_obliquity:.4f} -> Dec={mc_declination:.4f}")
            except Exception as mc_dec_err:
                logger.error(f"Error calculating Midheaven declination: {mc_dec_err}")
                if 'Midheaven' in positions and isinstance(positions['Midheaven'], dict): positions['Midheaven']['declination'] = None
        else:
            logger.warning("Cannot calculate AC/MC declinations: 'ascmc_raw' data missing or invalid in positions dict.")
    except Exception as e_acmc_dec:
        logger.error(f"General error calculating AC/MC declinations: {e_acmc_dec}", exc_info=True)
        if 'Ascendant' in positions and isinstance(positions['Ascendant'], dict): positions['Ascendant']['declination'] = None
        if 'Midheaven' in positions and isinstance(positions['Midheaven'], dict): positions['Midheaven']['declination'] = None

    logger.info("   Declination calculation finished.")
    return positions # Return the modified positions dictionary

def calculate_declination_aspects(positions, orb=DECLINATION_ORB):
    logger.info("   Calculating Declination Aspects (Parallel/Contra-Parallel)...")
    decl_aspects = defaultdict(list)
    processed_pairs = set() # To avoid duplicate aspect entries (e.g. Sun Parallel Moon and Moon Parallel Sun)

    if not positions:
        logger.warning("Declination aspect calculation skipped: Positions data is missing.")
        return {} # Return empty dict

    point_declinations = {}
    # Use DECLINATION_POINTS to define which points to check for these aspects
    for point_name in DECLINATION_POINTS:
        pos_data = positions.get(point_name)
        if isinstance(pos_data, dict) and pos_data.get('declination') is not None:
            try:
                point_declinations[point_name] = float(pos_data['declination'])
            except (ValueError, TypeError):
                logger.debug(f"Skipping {point_name} for declination aspects: invalid declination value '{pos_data.get('declination')}'.")
    
    valid_points_for_decl = list(point_declinations.keys())
    logger.debug(f"         Valid points for declination aspect calculation: {valid_points_for_decl}")

    if len(valid_points_for_decl) < 2:
        logger.info("   Not enough points with valid declinations to calculate aspects.")
        return {}

    for p1_name, p2_name in combinations(valid_points_for_decl, 2): # Use combinations
        dec1 = point_declinations[p1_name]
        dec2 = point_declinations[p2_name]
        
        # Parallel: Same declination, same hemisphere (both positive or both negative)
        # More accurately: declination values are very close.
        parallel_orb_actual = abs(dec1 - dec2)
        if parallel_orb_actual <= orb:
            # Check if they are in the same hemisphere (sign of declination)
            # This is implicit if abs(dec1-dec2) is small. If one is +20 and other is -20, abs(diff) is 40.
            # If one is +20 and other is +19, abs(diff) is 1.
            aspect_key = tuple(sorted((p1_name, p2_name))) + ('Parallel',) # Unique key for this aspect type and pair
            if aspect_key not in processed_pairs:
                aspect_detail = {"planet1": p1_name, "planet2": p2_name, "aspect": "Parallel", "orb": round(parallel_orb_actual, 2), "orb_limit": orb, "type": "declination"}
                decl_aspects[p1_name].append(aspect_detail)
                aspect_detail_rev = aspect_detail.copy(); aspect_detail_rev['planet1'] = p2_name; aspect_detail_rev['planet2'] = p1_name
                decl_aspects[p2_name].append(aspect_detail_rev)
                logger.debug(f"                    -> Decl Aspect Added: {p1_name} Parallel {p2_name} (Orb: {parallel_orb_actual:.2f}°, Decs: {dec1:.2f}°/{dec2:.2f}°)")
                processed_pairs.add(aspect_key)

        # Contra-Parallel: Same declination value, opposite hemisphere (one positive, one negative)
        # i.e., dec1 is approximately -dec2, so dec1 + dec2 is close to 0.
        contra_parallel_orb_actual = abs(dec1 + dec2)
        if contra_parallel_orb_actual <= orb:
            aspect_key = tuple(sorted((p1_name, p2_name))) + ('Contra-Parallel',)
            if aspect_key not in processed_pairs:
                aspect_detail = {"planet1": p1_name, "planet2": p2_name, "aspect": "Contra-Parallel", "orb": round(contra_parallel_orb_actual, 2), "orb_limit": orb, "type": "declination"}
                decl_aspects[p1_name].append(aspect_detail)
                aspect_detail_rev = aspect_detail.copy(); aspect_detail_rev['planet1'] = p2_name; aspect_detail_rev['planet2'] = p1_name
                decl_aspects[p2_name].append(aspect_detail_rev)
                logger.debug(f"                    -> Decl Aspect Added: {p1_name} Contra-Parallel {p2_name} (Orb: {contra_parallel_orb_actual:.2f}°, Decs: {dec1:.2f}°/{dec2:.2f}°)")
                processed_pairs.add(aspect_key)

    # Sort aspects for each planet by orb
    for planet_key in decl_aspects:
        decl_aspects[planet_key].sort(key=lambda x: x.get('orb', 99))
        
    logger.info(f"   Declination aspect calculation finished. Found aspects involving {len(decl_aspects)} points.")
    return dict(decl_aspects)


def calculate_future_transits( natal_positions, jd_ut_natal, start_date, duration_months, transiting_planets=None, natal_points=None, aspects_defs=None, orb=1.5, step_days=1):
    logger.info(f"Calculating future transits: Start={start_date}, Months={duration_months}, Orb={orb}, Step={step_days}d")
    if transiting_planets is None:
        transiting_planets = {'Mars': swe.MARS, 'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO, 'Chiron': swe.CHIRON}
        logger.debug(f"Using default transiting planets: {list(transiting_planets.keys())}")
    if natal_points is None:
        default_natal_points = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'North Node', 'True Node', 'Ascendant', 'Midheaven']
        natal_points = [p for p in default_natal_points if p in natal_positions and isinstance(natal_positions.get(p), dict) and natal_positions[p].get('sign') not in [None, 'Error']]
        logger.debug(f"Using filtered natal points: {natal_points}")
    if aspects_defs is None: # Should be MAJOR_TRANSIT_ASPECTS or similar
        logger.error("Aspect definitions (aspects_defs) are required for future transit calculation.")
        return []
    try:
        end_date = start_date + relativedelta(months=duration_months)
    except Exception as e:
        logger.error(f"Error calculating end date for transits: {e}")
        return []
    
    events = []
    active_aspects_tracker = {} # To track start, peak, min_orb, and potential end of an aspect
    previous_transit_signs = {} # To track planet ingresses
    flags = swe.FLG_SPEED | swe.FLG_SWIEPH # Calculate speed for retrograde checks if needed, though not strictly used for ingresses here
    
    date_iter = start_date
    logger.debug(f"Iterating for transits from {start_date} to {end_date}")

    while date_iter <= end_date:
        try:
            # Julian day for the current iteration date (at 00:00 UTC for simplicity)
            jd_current_iter = swe.julday(date_iter.year, date_iter.month, date_iter.day, 0.0, swe.GREG_CAL)
            
            current_transit_degrees = {}
            current_transit_signs = {}

            # Calculate positions of transiting planets for the current day
            for trans_planet_name, trans_planet_id in transiting_planets.items():
                calc_result, ret_flag = swe.calc_ut(jd_current_iter, trans_planet_id, flags)
                if ret_flag >= 0 and isinstance(calc_result, (list, tuple)) and len(calc_result) >= 1:
                    current_deg = calc_result[0] % 360.0
                    if current_deg < 0: current_deg += 360.0
                    current_transit_degrees[trans_planet_name] = current_deg
                    sign, _ = get_zodiac_sign(current_deg)
                    current_transit_signs[trans_planet_name] = sign
                else:
                    logger.warning(f"Could not calculate position for transiting {trans_planet_name} on {date_iter}")
                    current_transit_degrees[trans_planet_name] = None
                    current_transit_signs[trans_planet_name] = 'Error'

            # Check for Ingresses
            for trans_planet_name, current_sign in current_transit_signs.items():
                if current_sign == 'Error': continue
                
                prev_sign = previous_transit_signs.get(trans_planet_name)
                if prev_sign is None and date_iter == start_date: # Initialize on first day
                    previous_transit_signs[trans_planet_name] = current_sign
                elif prev_sign is not None and current_sign != prev_sign:
                    # Basic ingress detection (doesn't account for retrograde stationing exactly on cusp)
                    # More complex logic would check direction of motion if speed is available.
                    signs_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
                    try:
                        prev_idx = signs_order.index(prev_sign)
                        curr_idx = signs_order.index(current_sign)
                        # Check for forward motion into next sign or wrap-around from Pisces to Aries
                        if curr_idx == (prev_idx + 1) % 12:
                            ingress_event = {
                                'event_type': 'Ingress', 
                                'transiting_planet': trans_planet_name, 
                                'aspect': f"Enters {current_sign}", # Aspect here is the event description
                                'natal_point': None, # Not an aspect to a natal point
                                'sign': current_sign, 
                                'date_peak': date_iter, # Ingress happens on this day
                                'date_start': date_iter, 
                                'date_end': date_iter # Ingress is a point-in-time event for this simple model
                            }
                            events.append(ingress_event)
                            logger.debug(f"                    -> Ingress Detected: {ingress_event}")
                        else: # Could be retrograde out of sign, or skipped a sign (unlikely with daily steps)
                             logger.debug(f"Non-standard sign change for {trans_planet_name}: {prev_sign} -> {current_sign}. Not logged as standard ingress.")
                        previous_transit_signs[trans_planet_name] = current_sign
                    except ValueError: # Should not happen if signs are correct
                        logger.warning(f"Could not find sign index for {prev_sign} or {current_sign}. Ingress logic for {trans_planet_name} affected.")
                        previous_transit_signs[trans_planet_name] = current_sign


            # Check for Aspects
            for t_name, t_d in current_transit_degrees.items():
                if t_d is None: continue # Skip if transiting planet position couldn't be calculated

                for n_name in natal_points:
                    natal_data = natal_positions.get(n_name)
                    if not isinstance(natal_data, dict): continue # Skip if natal point data is not a dict
                    
                    natal_d = natal_data.get('degree')
                    if not isinstance(natal_d, (int, float)): # Ensure natal degree is valid
                        logger.debug(f"Skipping aspect check for transiting {t_name} to natal {n_name}: Invalid natal degree '{natal_d}'.")
                        continue

                    diff = abs(t_d - natal_d)
                    angular_distance = min(diff, 360.0 - diff) # Shortest arc

                    for asp_name, info in aspects_defs.items():
                        target_angle = info.get('angle', 0) # Get target angle for the aspect
                        current_orb_val = abs(angular_distance - target_angle)
                        
                        aspect_event_key = (t_name, n_name, asp_name)

                        if current_orb_val <= orb: # Aspect is within orb
                            if aspect_event_key not in active_aspects_tracker:
                                # New aspect entering orb
                                active_aspects_tracker[aspect_event_key] = {
                                    'start': date_iter, 
                                    'min_orb': current_orb_val, 
                                    'peak': date_iter, # Initially, peak is the start
                                    'end_temp': date_iter # Tentative end, updated each day it's in orb
                                }
                                logger.debug(f"                    -> Aspect Entering Orb: {aspect_event_key}, Orb={current_orb_val:.2f}")
                            else:
                                # Aspect continues to be in orb, update peak and temp end
                                if current_orb_val < active_aspects_tracker[aspect_event_key]['min_orb']:
                                    active_aspects_tracker[aspect_event_key]['min_orb'] = current_orb_val
                                    active_aspects_tracker[aspect_event_key]['peak'] = date_iter
                                active_aspects_tracker[aspect_event_key]['end_temp'] = date_iter
                        else: # Aspect is no longer within orb
                            if aspect_event_key in active_aspects_tracker:
                                # Aspect has just exited orb, record it
                                rec = active_aspects_tracker.pop(aspect_event_key)
                                end_date_final = rec.get('end_temp', date_iter - timedelta(days=step_days)) # Use last day it was in orb
                                event_data = {
                                    'event_type': 'Aspect', 
                                    'transiting_planet': t_name, 
                                    'natal_point': n_name, 
                                    'aspect': asp_name, 
                                    'date_start': rec['start'], 
                                    'date_peak': rec['peak'], 
                                    'date_end': end_date_final, 
                                    'orb_at_peak': round(rec['min_orb'], 2),
                                    'exact_angle': target_angle # Store the ideal aspect angle
                                }
                                events.append(event_data)
                                logger.debug(f"                    -> Aspect Exiting Orb: {aspect_event_key}, Orb={current_orb_val:.2f}, Recorded Event={event_data}")
        except Exception as loop_err:
            logger.error(f"Error during transit loop for date {date_iter}: {loop_err}", exc_info=True)
        
        date_iter += timedelta(days=step_days) # Move to next day

    # After loop, record any aspects that are still active at the end_date
    logger.debug(f"Processing {len(active_aspects_tracker)} transits still active at end date {end_date}")
    for aspect_event_key, rec in active_aspects_tracker.items():
        t_name, n_name, asp_name = aspect_event_key
        target_angle = aspects_defs.get(asp_name, {}).get('angle', '?') # Get target angle
        event_data = {
            'event_type': 'Aspect', 
            'transiting_planet': t_name, 
            'natal_point': n_name, 
            'aspect': asp_name, 
            'date_start': rec['start'], 
            'date_peak': rec['peak'], 
            'date_end': None, # Still active, so no end date
            'orb_at_peak': round(rec['min_orb'], 2),
            'exact_angle': target_angle
        }
        events.append(event_data)
        logger.debug(f"                    -> Recording Ongoing Aspect at end of period: {aspect_event_key}, Details={event_data}")
    
    logger.info(f"Future transit calculation finished. Found {len(events)} events.")
    # Sort events by start date, then peak date
    events.sort(key=lambda x: (x.get('date_start', x.get('date_peak', date.min if x.get('event_type') == 'Ingress' else date.max )), x.get('date_peak', date.min if x.get('event_type') == 'Ingress' else date.max)))
    return events


def get_current_transit_phase(age, natal_positions, orb=2.0): # Orb for checking current major transits
    logger.debug(f"Determining transit phase for age {age} with orb {orb}° for current major transits.")
    
    # Standard age-based life cycle transits
    if 28 <= age <= 30: return "First Saturn Return period"
    if 37 <= age <= 43: return "Uranus Opposition period" # Mid-life
    if 49 <= age <= 52: return "Chiron Return period"
    if 56 <= age <= 60: return "Second Saturn Return period"
    if 83 <= age <= 85: return "Uranus Return period"

    # Check for currently applying major transits from outer planets
    try:
        today = datetime.now(timezone.utc).date() # Use current UTC date
        jd_today = swe.julday(today.year, today.month, today.day, 0.0, swe.GREG_CAL)
        flags = swe.FLG_SWIEPH # Basic flags for position
        
        active_transit_strings = []
        
        for trans_planet_name, trans_planet_id in OUTER_TRANSIT_PLANETS.items():
            try:
                calc_result, ret_flag = swe.calc_ut(jd_today, trans_planet_id, flags)
                if ret_flag >= 0 and isinstance(calc_result, (list, tuple)) and len(calc_result) >= 1:
                    t_deg = calc_result[0] % 360.0
                    if t_deg < 0: t_deg += 360.0
                else:
                    logger.warning(f"Could not calculate current position for transiting {trans_planet_name}")
                    continue # Skip this transiting planet if position fails
            except Exception as calc_err:
                logger.error(f"Error calculating current position for transiting {trans_planet_name}: {calc_err}")
                continue

            # Natal points to check against
            points_to_check_against = ["Sun", "Moon", "Ascendant", "Midheaven"] # Could be expanded
            for natal_point_name in points_to_check_against:
                natal_data = natal_positions.get(natal_point_name, {})
                natal_deg = natal_data.get("degree")
                
                if not isinstance(natal_deg, (int, float)):
                    logger.debug(f"Skipping current transit check for {trans_planet_name} to {natal_point_name}: Invalid natal degree.")
                    continue

                diff = abs(t_deg - natal_deg)
                angular_distance = min(diff, 360.0 - diff)

                for asp_name, info in MAJOR_TRANSIT_ASPECTS.items(): # Defined globally or passed
                    target_angle = info["angle"]
                    current_orb_val = abs(angular_distance - target_angle)
                    if current_orb_val <= orb:
                        active_transit_strings.append(f"{trans_planet_name} {asp_name.lower()} {natal_point_name}")
        
        if active_transit_strings:
            unique_sorted_transits = sorted(list(set(active_transit_strings))) # Remove duplicates and sort
            return "Major current transits active: " + ", ".join(unique_sorted_transits)
            
    except Exception as e:
        logger.error(f"Error checking active major transits for current phase: {e}", exc_info=True)
    
    return "Integration Phase" # Default if no specific age or major transit matches


def calculate_fixed_star_conjunctions_v2( planet_positions_abs_deg, house_cusps, jd_ut, star_names=DEFAULT_FIXED_STAR_NAMES, orb=FIXED_STAR_ORB):
    matches = []
    logger.debug(f"--- Checking Fixed Star Conjunctions V2 for JD {jd_ut} ---")
    if not isinstance(planet_positions_abs_deg, dict):
        logger.warning("Invalid planet positions for fixed star check (V2).")
        return []
    if not jd_ut:
        logger.warning("Julian Day (jd_ut) required for fixed star calculation (V2).")
        return []
    if not house_cusps or len(house_cusps) < 12:
        logger.warning("House cusps required for fixed star house calculation (V2). Results will lack house info.")
        # Continue without house info if cusps are bad, but log it.
    if not star_names:
        logger.warning("No fixed star names provided or loaded for check (V2).")
        return []

    flags = swe.FLG_SWIEPH # Standard flags

    calculated_star_details = {} # Cache calculated star positions for this JD
    for star_name in star_names:
        if star_name in calculated_star_details: continue # Already processed

        star_deg_tropical = None; star_house = 0; star_sign = "Error"; star_exact_degree = 0.0

        try:
            # swe.fixstar_ut returns (xx,serr) where xx is a tuple of (lon, lat, dist, speedlon, speedlat, speeddist)
            # and serr is an error string if retflag < 0.
            # If star not found, serr contains "star ... not found".
            # If successful, serr is an empty string.
            star_data_tuple, error_string_or_empty = swe.fixstar_ut(star_name, jd_ut, flags)

            if error_string_or_empty and "not found" in error_string_or_empty.lower():
                logger.debug(f"Star '{star_name}' not found in ephemeris using swe.fixstar_ut.")
                calculated_star_details[star_name] = None
                continue
            elif error_string_or_empty: # Some other warning/error from swisseph
                logger.warning(f"Swisseph calculation Warning/Error for fixed star '{star_name}': {error_string_or_empty}")
                # Decide if to proceed or mark as None based on severity; for now, mark as None if any error string
                calculated_star_details[star_name] = None
                continue

            if isinstance(star_data_tuple, (list, tuple)) and len(star_data_tuple) >= 1 and isinstance(star_data_tuple[0], float):
                star_deg_tropical = star_data_tuple[0] % 360.0 # Ecliptical longitude
                if star_deg_tropical < 0: star_deg_tropical += 360.0
                
                star_sign, star_exact_degree = get_zodiac_sign(star_deg_tropical)
                if house_cusps and len(house_cusps) >= 12:
                    star_house = calculate_house(star_deg_tropical, house_cusps)
                else: star_house = 0 # No house info if cusps are bad
                
                calculated_star_details[star_name] = {
                    "degree": star_deg_tropical, 
                    "sign": star_sign, 
                    "exact_degree": star_exact_degree, 
                    "house": star_house
                }
            else: # Should not happen if error_string_or_empty was handled
                logger.warning(f"Unexpected data structure from swe.fixstar_ut for '{star_name}' even with no error string: {star_data_tuple}")
                calculated_star_details[star_name] = None

        except swe.Error as swe_err: # Catch specific Swisseph errors
            logger.error(f"Swisseph Error calculating fixed star '{star_name}': {swe_err}", exc_info=False)
            calculated_star_details[star_name] = None
        except Exception as star_calc_exception: # Catch any other unexpected errors
            logger.error(f"General Error calculating fixed star '{star_name}': {star_calc_exception}", exc_info=True)
            calculated_star_details[star_name] = None

    # Now check conjunctions
    for planet_name, planet_degree in planet_positions_abs_deg.items():
        if planet_degree is None: continue # Skip if planet degree is invalid
        try:
            planet_degree_float = float(planet_degree) % 360.0
            if planet_degree_float < 0: planet_degree_float += 360.0
        except (ValueError, TypeError):
            logger.warning(f"Invalid degree '{planet_degree}' for {planet_name} in fixed star check (V2).")
            continue

        for star_name, star_details in calculated_star_details.items():
            if star_details is None: continue # Skip if star calculation failed

            star_degree_float = star_details["degree"]
            difference = abs(planet_degree_float - star_degree_float)
            angular_distance = min(difference, 360.0 - difference) # Shortest arc

            if angular_distance <= orb:
                # Get pre-loaded info for this star
                basic_star_info = FIXED_STAR_INFO.get(star_name, {}) # FIXED_STAR_INFO should be loaded globally
                
                match_info = {
                    "star": star_name,
                    "star_info": { # Populate from FIXED_STAR_INFO
                        "magnitude": basic_star_info.get('magnitude', '?'),
                        "nature": basic_star_info.get('nature', 'Unknown'),
                        "keywords": basic_star_info.get('keywords', []),
                        "brief_interpretation": basic_star_info.get('brief_interpretation', '[Interpretation unavailable]'),
                        "mythology_link": basic_star_info.get('mythology_link', 'N/A')
                    },
                    "star_degree_tropical": round(star_degree_float, 4),
                    "star_sign": star_details["sign"],
                    "star_exact_degree": round(star_details["exact_degree"], 4),
                    "star_house": star_details["house"],
                    "linked_planet": planet_name,
                    "planet_degree_tropical": round(planet_degree_float, 4),
                    "orb": round(angular_distance, 2)
                }
                matches.append(match_info)
                logger.debug(f"  -> Match V2: {planet_name} ({planet_degree_float:.2f}°) conjunct {star_name} ({star_details['exact_degree']:.2f}° {star_details['sign']} H{star_details['house']}), Orb: {angular_distance:.2f}°")

    logger.debug(f"--- Fixed Star Check V2 Complete: Found {len(matches)} matches ---")
    matches.sort(key=lambda item: item['orb']) # Sort by tightest orb
    return matches


# === Main Calculation Function ===
def calculate_chart(
    year, month, day, hour, minute, lat, lng, city, country, tz_str, gender,
    ephemeris_path_used, # This path should be validated and used
    skip_fixed_stars=False,
    full_name=None, # For numerology
    house_system=b"P" # Default to Placidus (byte string)
):
    """Calculate complete birth chart including new calculations."""
    # --- PATCH: Ensure ephemeris path is set at the beginning ---
    if ephemeris_path_used and os.path.isdir(ephemeris_path_used):
        swe.set_ephe_path(ephemeris_path_used)
        logger.info(f"Swiss Ephemeris path explicitly set to: {ephemeris_path_used} within calculate_chart.")
    elif not ephemeris_path_used : # If path is None or empty string
        logger.warning(f"No ephemeris_path_used provided to calculate_chart. Swisseph might use its default or previously set path.")
    elif not os.path.isdir(ephemeris_path_used): # If path provided but invalid
        logger.error(f"CRITICAL: Provided Swiss Ephemeris path is invalid or does not exist: {ephemeris_path_used}. Calculation may fail or use defaults.")
    # --- END OF PATCH ---

    chart_version = __version__
    logger.info(f"--- Starting Chart Calculation (V{chart_version}) ---")
    logger.info(f"   Input: {day}-{month}-{year} {hour:02d}:{minute:02d}, Loc: '{city}', TZ: {tz_str}, Name: {full_name}")
    calculation_start_utc = datetime.now(timezone.utc)
    jd_ut = None # Julian Day Universal Time

    # Convert local birth time to UTC and then to Julian Day
    try:
        local_dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz_str))
        utc_dt = local_dt.astimezone(timezone.utc)
        jd_ut = swe.julday(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0, # Convert time to decimal hour
            swe.GREG_CAL # Use Gregorian calendar
        )
        logger.info("   Time Conversion Success.")
        logger.debug(f"         Local ({tz_str}): {local_dt}, UTC: {utc_dt}, JD_UT: {jd_ut}")
    except ZoneInfoNotFoundError:
        logger.error(f"Unknown or invalid Timezone String provided: '{tz_str}'")
        # This should be a critical error, preventing further calculation
        raise ValueError(f"Unknown Timezone: {tz_str}")
    except Exception as e:
        logger.error(f"Timezone/JD calculation failed: {e}", exc_info=True)
        raise RuntimeError(f"Timezone/JD calculation failed: {e}") from e

    # Geocoding (optional, for validating city/country if geopy is available)
    geo_city = "[Geocoding Skipped/Failed]"; geo_country = "[Geocoding Skipped/Failed]"
    if _geopy_available:
        try:
            geolocator = Nominatim(user_agent=f"astro_calc_{chart_version}") # Unique user agent
            location = geolocator.reverse((lat, lng), exactly_one=True, language='en', timeout=10)
            if location and location.raw and 'address' in location.raw:
                address = location.raw['address']
                geo_city = address.get('city') or address.get('town') or address.get('village') or "[City N/A]"
                geo_country = address.get('country', "[Country N/A]")
                logger.info(f"   Geocoding successful: {geo_city}, {geo_country}")
            else:
                logger.warning("Geocoding returned no address data.")
        except Exception as geo_e:
            logger.warning(f"Geocoding failed: {geo_e}")
    else:
        logger.info("   Geocoding skipped (geopy not available).")

    # Calculate House Cusps and Angles (Ascendant, MC)
    house_cusps = []; ascendant_deg = None; mc_deg = None; ascmc_data = []
    try:
        # swe.houses returns (cusps_array, ascmc_array)
        houses_data, ascmc_data = swe.houses(jd_ut, lat, lng, house_system)
        house_cusps = list(houses_data[:12]) # First 12 are house cusps 1-12
        ascendant_deg = ascmc_data[0]    # Ascendant
        mc_deg = ascmc_data[1]           # Midheaven (MC)
        
        # Validate house calculation results
        if len(house_cusps) != 12 or any(c is None for c in house_cusps) or ascendant_deg is None or mc_deg is None:
            logger.error("House calculation returned invalid cusp or angle data.")
            # This is where the original return statement was misplaced.
            # It should be part of this try-except block or the main function's error handling.
            return {"error": "House calculation invalid cusp/angle data."} # Correctly indented now
            
        logger.info("   House Cusps Calculated.")
        logger.debug(f"         Raw Cusps: {house_cusps}")
        logger.debug(f"         Raw Asc/MC: Asc={ascmc_data[0]}, MC={ascmc_data[1]}")
    except Exception as e:
        logger.error(f"House calculation failed: {e}", exc_info=True)
        return {"error": f"House calculation failed: {e}"}


    # Initialize chart dictionary structure
    chart = {
        "calculation_info": {
            "version": chart_version,
            "calculation_timestamp_utc": calculation_start_utc.isoformat(),
            "swisseph_version": swe.version,
            "ephemeris_path": ephemeris_path_used,
        },
        "birth_details": {
            "year": year, "month": month, "day": day, "hour": hour, "minute": minute,
            "latitude": lat, "longitude": lng,
            "city": city, "country": country, "tz_str": tz_str,
            "geo_validated_city": geo_city, "geo_validated_country": geo_country,
            "house_system": house_system.decode('utf-8', 'ignore'), # Decode bytes to string
            "gender": gender,
            "age": "Error", "day_of_week": "Error", "chart_ruler": "Error",
            "hemisphere": "Unknown" 
        },
        "house_info": {
            "cusps": house_cusps, # Degrees of house cusps 1-12
            "ascmc_raw": list(ascmc_data) # Store full ascmc array for reference if needed
        },
        "positions": {}, # Will store planet/point data (degree, sign, house, speed, retro, dignity, declination)
        "angles": {},    # Will store Asc, MC, IC, DC data
        "aspects": defaultdict(list), # Aspects between points
        "declination_aspects": defaultdict(list), # Parallel/Contra-parallel
        "midpoints": {},
        "aspect_patterns": [], # Grand Trines, T-Squares, etc.
        "house_rulers": {},
        "numerology": {
            "Life Path Number": {"number": 0, "meaning": ""}, # Meaning to be added if desired
            "Personal Year": {"number": 0, "meaning": ""}, # Meaning to be added
            "Soul Urge Number": {"number": 0},
            "Expression Number": {"number": 0},
        },
        "earth_energies": {
            "schumann": {"frequency": None, "source": "error"}, # Placeholder
            "moon_phase": {"name": "Error", "percent_illuminated": 0.0, "angle": 0.0}
        },
        "elemental_balance": {}, # Percentages of Fire, Earth, Air, Water
        "modality_balance": {},  # Percentages of Cardinal, Fixed, Mutable
        "chart_signatures": { # Summary interpretations
            "dominant_element": "Error", "weakest_element": "Error",
            "dominant_modality": "Error", "weakest_modality": "Error", # Added weakest modality
            "unaspected_planets_str": "Error",
            "prompt_dominant_element_1": "None", 
            "prompt_dominant_element_2": "None", 
            "prompt_least_represented_element": "None"
        },
        "other_points": { # For Parts, Vertex etc.
            "Part of Fortune": {},
            "Part of Spirit": {}
        },
        "transits_current": {}, # Placeholder for current transits to natal
        "future_transits": [],  # List of significant future transit events
        "current_transit_phase": "Unknown", # E.g., "Saturn Return"
        "fixed_star_links": [] # Conjunctions to fixed stars
    }

    # Calculate Age and Day of the Week
    try:
        today_utc = calculation_start_utc.date() # Use consistent date for age calculation
        birthdate = date(year, month, day)
        # More precise age calculation considering month/day
        age_calculated = today_utc.year - birthdate.year - ((today_utc.month, today_utc.day) < (birthdate.month, birthdate.day))
        chart['birth_details']['age'] = age_calculated
        chart['birth_details']['day_of_week'] = birthdate.strftime('%A') # Full day name
        logger.info(f"   Calculated Age: {age_calculated}, Day of Week: {chart['birth_details']['day_of_week']}")
    except Exception as e:
        logger.warning(f"Age/Day of Week calculation error: {e}")
        # chart['birth_details']['age'] and 'day_of_week' will remain "Error"

    # Determine Hemisphere
    logger.info("   Calculating Hemisphere...")
    hemisphere_result = "Unknown"
    latitude_val = chart['birth_details'].get("latitude", None) # Use the validated latitude if available
    if latitude_val is not None:
        try:
            lat_float = float(latitude_val)
            hemisphere_result = "Northern Hemisphere" if lat_float >= 0 else "Southern Hemisphere"
        except (ValueError, TypeError):
            hemisphere_result = "Unknown (Invalid Lat)"
    else:
        hemisphere_result = "Unknown (Missing Lat)"
    chart['birth_details']['hemisphere'] = hemisphere_result
    logger.info(f"         Hemisphere determined: {hemisphere_result}")


    # Populate Angles (Asc, MC, IC, DC) and determine Chart Ruler
    logger.info("   Populating Angles & Chart Ruler...")
    try:
        asc_sign, asc_exact = get_zodiac_sign(ascendant_deg); asc_house = 1 # Ascendant is always cusp of 1st house
        chart['angles']['Ascendant'] = {'degree': ascendant_deg, 'sign': asc_sign, 'exact_degree': asc_exact, 'house': asc_house}
        chart['positions']['Ascendant'] = chart['angles']['Ascendant'] # Also add to positions for aspecting
        logger.debug(f"         Ascendant: {asc_sign} {asc_exact:.4f}°")

        mc_sign, mc_exact = get_zodiac_sign(mc_deg); mc_house = 10 # MC is always cusp of 10th house in many systems (like Placidus)
        chart['angles']['Midheaven'] = {'degree': mc_deg, 'sign': mc_sign, 'exact_degree': mc_exact, 'house': mc_house}
        chart['positions']['Midheaven'] = chart['angles']['Midheaven']
        logger.debug(f"         Midheaven: {mc_sign} {mc_exact:.4f}°")

        ic_deg = (mc_deg + 180.0) % 360.0 # IC is opposite MC
        ic_sign, ic_exact = get_zodiac_sign(ic_deg); ic_house = 4 # IC is cusp of 4th house
        chart['angles']['IC'] = {'degree': ic_deg, 'sign': ic_sign, 'exact_degree': ic_exact, 'house': ic_house}
        chart['positions']['IC'] = chart['angles']['IC']
        logger.debug(f"         IC: {ic_sign} {ic_exact:.4f}°")

        dc_deg = (ascendant_deg + 180.0) % 360.0 # Descendant is opposite Ascendant
        dc_sign, dc_exact = get_zodiac_sign(dc_deg); dc_house = 7 # DC is cusp of 7th house
        chart['angles']['DC'] = {'degree': dc_deg, 'sign': dc_sign, 'exact_degree': dc_exact, 'house': dc_house}
        chart['positions']['DC'] = chart['angles']['DC']
        logger.debug(f"         Descendant: {dc_sign} {dc_exact:.4f}°")

        if asc_sign != "Error":
            chart_ruler_result = TRADITIONAL_RULER_MAP.get(asc_sign, "Error")
            chart['birth_details']['chart_ruler'] = chart_ruler_result
            logger.info(f"         Chart Ruler (Traditional): {chart_ruler_result}")
        else:
            chart['birth_details']['chart_ruler'] = "Error (Asc Sign Error)"
            logger.warning("Cannot determine chart ruler due to Ascendant sign error.")
    except Exception as e:
        logger.error(f"Error populating angles or chart ruler: {e}", exc_info=True)
        # Ensure defaults if error
        for angle_key in ['Ascendant', 'Midheaven', 'IC', 'DC']:
            if angle_key not in chart['angles']: chart['angles'][angle_key] = {'degree': None, 'sign': 'Error', 'exact_degree': 0.0, 'house': 0}
            if angle_key not in chart['positions']: chart['positions'][angle_key] = chart['angles'][angle_key]
        if 'chart_ruler' not in chart['birth_details']: chart['birth_details']['chart_ruler'] = "Error (Calc Exception)"


    # Calculate Natal Planet/Point Positions
    if jd_ut is None: # Should have been caught by now, but double check
        logger.error("CRITICAL: Julian Day (jd_ut) is None. Cannot calculate planetary positions.")
        return {"error": "Failed to calculate Julian Day for position calculation."}

    logger.info("   Calculating Natal Positions...")
    # Define bodies to calculate
    bodies_for_calc = {
        'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS, 'Mars': swe.MARS,
        'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO,
        'North Node': swe.MEAN_NODE, # Mean Node
        'True Node': swe.TRUE_NODE,   # True Node
        'Chiron': swe.CHIRON,
        'Ceres': swe.CERES, 'Pallas': swe.PALLAS, 'Juno': swe.JUNO, 'Vesta': swe.VESTA,
        'Black Moon Lilith': swe.MEAN_APOG # Mean Apogee (Lilith)
    }
    flags = swe.FLG_SPEED | swe.FLG_SWIEPH # Request speed for retrograde detection
    sun_pos_deg = None # To store Sun's degree for Moon Phase calculation
    moon_pos_deg = None # To store Moon's degree for Moon Phase
    
    temp_positions_for_decl_calc = {} # For passing to declination calculation

    for name, body_id in bodies_for_calc.items():
        sign, exact_degree, house, speed, is_retrograde, degree = 'Error', 0.0, 0, 0.0, False, None
        dignity = "None"
        try:
            calc_result, ret_flag = swe.calc_ut(jd_ut, body_id, flags)
            if ret_flag < 0: # Error or warning from Swisseph
                logger.warning(f"Swisseph calculation warning/error for {name}. Return flag: {ret_flag}.")
                # If calc_result is a string, it's an error message
                if isinstance(calc_result, str): logger.warning(f"  Swisseph message for {name}: {calc_result}")

            if isinstance(calc_result, (list, tuple)) and len(calc_result) >= 4: # Expected result structure
                pos_data = calc_result
                degree = pos_data[0] # Ecliptical longitude
                speed = pos_data[3]  # Speed in longitude
                is_retrograde = speed < 0
                sign, exact_degree = get_zodiac_sign(degree)
                if sign != 'Error':
                    if house_cusps and len(house_cusps) >= 12: # Ensure valid cusps
                        house = calculate_house(degree, chart['house_info']['cusps'])
                    else:
                        house = 0 # Cannot determine house
                    # Get essential dignity
                    if name in ESSENTIAL_DIGNITY_RULES:
                        dignity = get_essential_dignity(name, sign)
                else: # Sign calculation error
                    house = 0 # Cannot determine house if sign is error

                if name == 'Sun': sun_pos_deg = degree
                if name == 'Moon': moon_pos_deg = degree

                logger.debug(f"         {name}: {sign} {exact_degree:.4f}°, House {house}, Speed {speed:.4f}{' R' if is_retrograde else ''}, Dignity: {dignity}")
            else: # Unexpected result from swe.calc_ut
                logger.error(f"Unexpected result structure from swe.calc_ut for {name}: {calc_result}")
                sign = "Error (Calc Result Structure)" # Mark as error

        except Exception as e:
            logger.error(f"Error calculating {name}: {e}", exc_info=False) # exc_info=False for brevity in loop
            sign = "Error (Exception)"
            degree = None # Ensure degree is None if calculation fails

        chart['positions'][name] = {
            'degree': degree, 'sign': sign, 'exact_degree': exact_degree, 'house': house,
            'speed': round(speed, 6), 'is_retrograde': is_retrograde, 'dignity': dignity,
            'declination': None # Placeholder, will be filled by calculate_declinations
        }
        if degree is not None: # Only add to declination list if degree was calculated
             temp_positions_for_decl_calc[name] = body_id


    # Calculate Declinations (after all main body positions are set)
    if jd_ut is None:
        logger.error("Cannot calculate declinations because Julian Day (jd_ut) is not valid.")
    else:
        # Pass only the bodies for which we successfully got degrees
        chart['positions'] = calculate_declinations(jd_ut, temp_positions_for_decl_calc, chart['positions'])
        # Remove ascmc_raw from positions if it was temporarily stored there by mistake
        chart['positions'].pop('ascmc_raw', None) # Ensure it's not in final positions

    # Calculate South Node (opposite North Node)
    logger.info("   Calculating South Node position...")
    north_node_pos_data = chart['positions'].get('North Node') # Use Mean Node for SN generally
    if north_node_pos_data and north_node_pos_data.get('sign') != 'Error' and north_node_pos_data.get('degree') is not None:
        try:
            nn_degree = north_node_pos_data['degree']
            sn_degree = (nn_degree + 180.0) % 360.0 # Opposite degree
            sn_sign, sn_exact_degree = get_zodiac_sign(sn_degree)
            sn_house = 0
            sn_declination = None
            if sn_sign != 'Error':
                if house_cusps and len(house_cusps) >= 12: # Valid cusps needed for house
                    sn_house = calculate_house(sn_degree, chart['house_info']['cusps'])
                else:
                    sn_house = 0
                # South Node declination is opposite to North Node's
                if north_node_pos_data.get('declination') is not None:
                    try:
                        sn_declination = -float(north_node_pos_data['declination'])
                    except (ValueError, TypeError):
                        sn_declination = None
            else: # Sign error for SN
                sn_house = 0
            
            # South Node speed is same as North Node's but opposite sign (Nodes usually retrograde)
            sn_speed = -north_node_pos_data.get('speed', 0.0) 
            sn_is_retrograde = sn_speed < 0 # Usually true for nodes

            chart['positions']['South Node'] = {
                'degree': sn_degree, 'sign': sn_sign, 'exact_degree': sn_exact_degree,
                'house': sn_house, 'speed': round(sn_speed, 6), 'is_retrograde': sn_is_retrograde,
                'dignity':'None', # Nodes don't typically have dignity in this system
                'declination': sn_declination
            }
            sn_decl_str = "?"
            if sn_declination is not None:
                 try: sn_decl_str = f"{sn_declination:.4f}°"
                 except (TypeError, ValueError): pass # Keep as "?" if formatting fails

            logger.debug(f"         South Node: {sn_sign} {sn_exact_degree:.4f}°, House {sn_house}, Dec {sn_decl_str}")
        except Exception as e:
            logger.error(f"Error calculating South Node: {e}", exc_info=False)
            chart['positions']['South Node'] = {'degree': None, 'sign': 'Error', 'exact_degree': 0.0, 'house': 0, 'speed': 0.0, 'is_retrograde': False, 'dignity':'None', 'declination': None}
    else:
        logger.warning("South Node calculation skipped: North Node data missing or invalid.")
        chart['positions']['South Node'] = {'degree': None, 'sign': 'Error', 'exact_degree': 0.0, 'house': 0, 'speed': 0.0, 'is_retrograde': False, 'dignity':'None', 'declination': None}

    # Calculate Elemental and Modality Balances
    logger.info("   Calculating Elemental and Modality Balances...")
    element_counts = Counter(); modality_counts = Counter(); valid_points_for_balance = 0
    dominant_element_str = "None"; weakest_element_str = "None"; dominant_modality_str = "None"; weakest_modality_str = "None" # Initialize
    try:
        for point_name_bal in POINTS_FOR_BALANCE: # Use predefined list of points for balance
            pos_data_bal = chart['positions'].get(point_name_bal)
            if isinstance(pos_data_bal, dict) and pos_data_bal.get('sign') not in [None, 'Error']:
                sign_bal = pos_data_bal['sign']
                element_bal = ELEMENT_MAP.get(sign_bal)
                modality_bal = MODALITY_MAP.get(sign_bal)
                if element_bal: element_counts[element_bal] += 1
                if modality_bal: modality_counts[modality_bal] += 1
                valid_points_for_balance += 1
        
        if valid_points_for_balance > 0:
            # Calculate percentages
            chart['elemental_balance'] = {el: round((count / valid_points_for_balance) * 100, 1) for el, count in element_counts.items()}
            chart['modality_balance'] = {mod: round((count / valid_points_for_balance) * 100, 1) for mod, count in modality_counts.items()}

            # Determine dominant and weakest elements
            if element_counts:
                max_elem_count = max(element_counts.values())
                dominant_element_list_val = sorted([k for k, v_el in element_counts.items() if v_el == max_elem_count])
                dominant_element_str = "/".join(dominant_element_list_val)
                
                all_elements_set = set(ELEMENT_MAP.values()) # {"Fire", "Earth", "Air", "Water"}
                min_elem_count = min(element_counts.values()) if element_counts else 0
                # Weakest are those with min count AND not dominant, PLUS any missing elements
                weakest_elements_with_count = sorted([k for k, v_el in element_counts.items() if v_el == min_elem_count and k not in dominant_element_list_val])
                missing_elements_list = sorted(list(all_elements_set - set(element_counts.keys())))
                full_weakest_list_val = sorted(list(set(missing_elements_list + weakest_elements_with_count)))
                
                if set(dominant_element_list_val) == set(full_weakest_list_val) and len(element_counts) == 1: # e.g. only Fire planets
                     weakest_element_str = "N/A (Only Dominant Present)"
                elif not full_weakest_list_val and len(set(element_counts.values())) == 1 and len(element_counts) == len(all_elements_set): # All elements equally represented
                    weakest_element_str = "Balanced"
                else:
                     weakest_element_str = "/".join(full_weakest_list_val) if full_weakest_list_val else "None" # if somehow list is empty but not balanced

            # Determine dominant and weakest modalities
            if modality_counts:
                max_mod_count = max(modality_counts.values())
                dominant_modality_list_val = sorted([k_mod for k_mod, v_mod in modality_counts.items() if v_mod == max_mod_count])
                dominant_modality_str = "/".join(dominant_modality_list_val)

                all_modalities_set = set(MODALITY_MAP.values()) # {"Cardinal", "Fixed", "Mutable"}
                min_mod_count = min(modality_counts.values()) if modality_counts else 0
                weakest_modality_list_val = sorted([k_mod for k_mod, v_mod in modality_counts.items() if v_mod == min_mod_count and k_mod not in dominant_modality_list_val])
                missing_modalities_list = sorted(list(all_modalities_set - set(modality_counts.keys())))
                full_weakest_mod_list_val = sorted(list(set(missing_modalities_list + weakest_modality_list_val)))

                if set(dominant_modality_list_val) == set(full_weakest_mod_list_val) and len(modality_counts) == 1:
                    weakest_modality_str = "N/A (Only Dominant Present)"
                elif not full_weakest_mod_list_val and len(set(modality_counts.values())) == 1 and len(modality_counts) == len(all_modalities_set):
                    weakest_modality_str = "Balanced"
                else:
                    weakest_modality_str = "/".join(full_weakest_mod_list_val) if full_weakest_mod_list_val else "None"
            
            chart['chart_signatures']['dominant_element'] = dominant_element_str
            chart['chart_signatures']['weakest_element'] = weakest_element_str
            chart['chart_signatures']['dominant_modality'] = dominant_modality_str
            chart['chart_signatures']['weakest_modality'] = weakest_modality_str # Storing weakest modality too

            # --- PATCH 7.42.2: Prompt-ready elements ---
            prompt_dom_elem_1_val = "None"
            prompt_dom_elem_2_val = "None" # Secondary dominant if exists
            prompt_least_rep_elem_val = "None"

            if dominant_element_str not in ["None", "Error"]:
                dom_list_parsed_val = dominant_element_str.split('/')
                prompt_dom_elem_1_val = dom_list_parsed_val[0]
                if len(dom_list_parsed_val) > 1: # Co-dominant
                    prompt_dom_elem_2_val = dom_list_parsed_val[1]
                else: # Single dominant, find next highest for prompt_dom_elem_2
                    current_element_balance_data_val = chart.get('elemental_balance', {})
                    if current_element_balance_data_val:
                        sorted_elems_val = sorted(
                            [(el_s, pct_s) for el_s, pct_s in current_element_balance_data_val.items() if el_s != prompt_dom_elem_1_val],
                            key=lambda item_s: item_s[1], # Sort by percentage
                            reverse=True
                        )
                        if sorted_elems_val: # If there are other elements
                            prompt_dom_elem_2_val = sorted_elems_val[0][0]
            
            if weakest_element_str not in ["None", "Error", "N/A (Only Dominant Present)", "Balanced"]:
                weak_list_parsed_val = weakest_element_str.split('/')
                prompt_least_rep_elem_val = weak_list_parsed_val[0] # Take the first if multiple weakest/missing
            elif weakest_element_str == "Balanced":
                 prompt_least_rep_elem_val = "perfectly balanced"
            elif weakest_element_str == "N/A (Only Dominant Present)":
                 prompt_least_rep_elem_val = "other elements less emphasized"


            chart['chart_signatures']['prompt_dominant_element_1'] = prompt_dom_elem_1_val
            # Ensure prompt_dom_elem_2 is not same as 1, and not "None" if it was derived
            chart['chart_signatures']['prompt_dominant_element_2'] = prompt_dom_elem_2_val if prompt_dom_elem_2_val != prompt_dom_elem_1_val and prompt_dom_elem_2_val != "None" else "None"
            chart['chart_signatures']['prompt_least_represented_element'] = prompt_least_rep_elem_val
            logger.info(f"         Prompt Elements: Dom1='{chart['chart_signatures']['prompt_dominant_element_1']}', Dom2='{chart['chart_signatures']['prompt_dominant_element_2']}', Least='{chart['chart_signatures']['prompt_least_represented_element']}'")
            # --- END PATCH ---
            logger.info(f"         Balances Calculated (based on {valid_points_for_balance} points): Elements={chart['elemental_balance']}, Modalities={chart['modality_balance']}")
            logger.info(f"         Dominant Element(s): {dominant_element_str}, Weakest: {weakest_element_str}")
            logger.info(f"         Dominant Modality(ies): {dominant_modality_str}, Weakest: {weakest_modality_str}")
        else: # No valid points for balance
            logger.warning("Balance calculation skipped: No valid points found.")
            for key_sig_bal_err in ['dominant_element', 'weakest_element', 'dominant_modality', 'weakest_modality', 'prompt_dominant_element_1', 'prompt_dominant_element_2', 'prompt_least_represented_element']:
                chart['chart_signatures'][key_sig_bal_err] = "Error (No Points)"
    except Exception as e_bal_main:
        logger.error(f"Error calculating balances: {e_bal_main}", exc_info=True)
        for key_sig_err_main in ['dominant_element', 'weakest_element', 'dominant_modality', 'weakest_modality', 'prompt_dominant_element_1', 'prompt_dominant_element_2', 'prompt_least_represented_element']:
            chart['chart_signatures'][key_sig_err_main] = "Error (Calc Exception)"


    # Calculate Aspects (Longitude)
    chart['aspects'] = calculate_aspects(chart['positions'])
    # Calculate Declination Aspects
    chart['declination_aspects'] = calculate_declination_aspects(chart['positions'], orb=DECLINATION_ORB)

    # Detect Aspect Patterns
    logger.info("   Detecting Rare Aspect Patterns...")
    all_patterns = []
    patterns_found_summary = [] # For logging
    try:
        all_patterns.extend(detect_grand_trine(chart.get('aspects',{}), chart.get('positions',{})))
        all_patterns.extend(detect_t_square(chart.get('aspects',{})))
        all_patterns.extend(detect_yod(chart.get('aspects',{})))
        all_patterns.extend(detect_grand_cross(chart.get('aspects',{})))
        all_patterns.extend(detect_stellium(chart.get('positions',{}))) # Uses positions
        chart['aspect_patterns'] = all_patterns
        if all_patterns:
            patterns_found_summary = [f"{p['pattern']} ({','.join(p.get('points',[]))})" for p in all_patterns if isinstance(p,dict)]
            logger.info(f"         Aspect Patterns Detected: {'; '.join(patterns_found_summary)}")
        else:
            logger.info("         No major aspect patterns detected.")
    except Exception as e:
        logger.error(f"Error detecting aspect patterns: {e}", exc_info=True)
        chart['aspect_patterns'] = [] # Ensure it's an empty list on error

    # Identify Unaspected Planets
    logger.info("   Identifying unaspected planets (major aspects only)...")
    unaspected_planets = []
    unaspected_planets_str = "None" # Default string
    try:
        planets_to_check_unaspected = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron']
        major_aspect_names_set = {name for name, info in ASPECT_DEFINITIONS.items() if info.get('type') == 'major'}
        
        all_longitude_aspects_list = [] # Flattened list of all longitude aspects
        for p_name_aspect, aspects_list_for_p in chart.get('aspects', {}).items():
            if isinstance(aspects_list_for_p, list):
                all_longitude_aspects_list.extend(aspects_list_for_p)
        
        aspected_planets_set = set()
        processed_aspect_pairs_unaspected = set() # To avoid double counting from p1-p2 and p2-p1 entries
        for aspect_detail in all_longitude_aspects_list:
            if isinstance(aspect_detail, dict) and aspect_detail.get('aspect') in major_aspect_names_set:
                p1 = aspect_detail.get('planet1')
                p2 = aspect_detail.get('planet2')
                # Only consider pairs involving planets_to_check_unaspected
                if p1 in planets_to_check_unaspected and p2 in planets_to_check_unaspected:
                    pair = tuple(sorted((p1,p2)))
                    if pair not in processed_aspect_pairs_unaspected:
                        aspected_planets_set.add(p1)
                        aspected_planets_set.add(p2)
                        processed_aspect_pairs_unaspected.add(pair)

        unaspected_planets = [p for p in planets_to_check_unaspected 
                              if p in chart['positions'] and isinstance(chart['positions'].get(p), dict) and chart['positions'][p].get('sign') != 'Error' # Must be valid point
                              and p not in aspected_planets_set]
        
        unaspected_planets_str = ", ".join(sorted(unaspected_planets)) if unaspected_planets else "None"
        chart['chart_signatures']['unaspected_planets_str'] = unaspected_planets_str
        logger.info(f"         Unaspected planets identified: {unaspected_planets_str}")
    except Exception as e:
        logger.error(f"Error identifying unaspected planets: {e}", exc_info=True)
        chart['chart_signatures']['unaspected_planets_str'] = "Error"


    # Calculate House Rulers
    logger.info("   Calculating House Rulers (Traditional)...")
    house_rulers = {}
    try:
        for i in range(12):
            house_num = i + 1
            cusp_deg = chart['house_info']['cusps'][i]
            if cusp_deg is None: # Should have been caught earlier by house calc validation
                logger.warning(f"Skipping House {house_num} ruler: Cusp degree is None.")
                house_rulers[f'House {house_num}'] = {"ruler": "Error", "sign": "Error"}
                continue
            
            cusp_sign, _ = get_zodiac_sign(cusp_deg)
            ruler = "Error" # Default
            if cusp_sign != "Error":
                ruler = TRADITIONAL_RULER_MAP.get(cusp_sign, "Error") # Find ruler from map
            else:
                logger.warning(f"Cannot determine ruler for House {house_num}: Cusp sign calculation error.")
            house_rulers[f'House {house_num}'] = {"ruler": ruler, "sign": cusp_sign}
            logger.debug(f"         House {house_num}: Cusp={cusp_sign}, Ruler={ruler}")
        chart['house_rulers'] = house_rulers
        logger.info("         House ruler calculation complete.")
    except Exception as e:
        logger.error(f"Error calculating house rulers: {e}", exc_info=True)
        chart['house_rulers'] = {f'House {i+1}': {"ruler": "Error", "sign": "Error"} for i in range(12)}


    # Numerology Calculations
    logger.info("   Calculating Numerology...")
    try:
        # Life Path: sum of (sum_digits(day) + sum_digits(month) + sum_digits(year)) then reduce
        lp_sum = sum_digits(day) + sum_digits(month) + sum_digits(year)
        lp_number = reduce_number(lp_sum)
        chart['numerology']['Life Path Number']['number'] = lp_number
        # chart['numerology']['Life Path Number']['meaning'] = "Meaning for " + str(lp_number) # Placeholder for meaning
        logger.debug(f"         Life Path Number: {lp_number} (Raw Sum: {lp_sum})")

        # Personal Year: sum of (sum_digits(day) + sum_digits(month) + sum_digits(current_year)) then reduce
        current_year = calculation_start_utc.year # Use year of calculation for Personal Year
        py_sum = sum_digits(day) + sum_digits(month) + sum_digits(current_year)
        py_number = reduce_number(py_sum)
        chart['numerology']['Personal Year']['number'] = py_number
        # chart['numerology']['Personal Year']['meaning'] = "Meaning for PY " + str(py_number) # Placeholder
        logger.debug(f"         Personal Year ({current_year}): {py_number} (Raw Sum: {py_sum})")

        if full_name: # Calculate Soul Urge and Expression if name is provided
            soul_urge_num = _calculate_soul_urge(full_name)
            expression_num = _calculate_expression(full_name)
            chart['numerology']['Soul Urge Number']['number'] = soul_urge_num
            chart['numerology']['Expression Number']['number'] = expression_num
            logger.debug(f"         Soul Urge: {soul_urge_num}, Expression: {expression_num} (Name: {full_name})")
        else:
            logger.info("         Soul Urge & Expression calculation skipped: No full name provided.")
            chart['numerology']['Soul Urge Number']['number'] = 0 # Or None
            chart['numerology']['Expression Number']['number'] = 0 # Or None
        logger.info("         Numerology calculation complete.")
    except Exception as e:
        logger.error(f"Error calculating numerology: {e}", exc_info=True)
        # Ensure default error values if calculation fails
        for key in chart['numerology']: chart['numerology'][key]['number'] = 0

    # Moon Phase
    if jd_ut is None:
        logger.error("Cannot calculate Moon Phase because Julian Day (jd_ut) is not valid.")
        chart['earth_energies']['moon_phase'] = {"name": "Error", "percent_illuminated": 0.0, "angle": 0.0}
    else:
        logger.info("   Calculating Moon Phase...")
        moon_phase_details = get_moon_phase_details(jd_ut, sun_pos_deg, moon_pos_deg)
        chart['earth_energies']['moon_phase'] = moon_phase_details
        logger.info(f"         Moon Phase: {moon_phase_details.get('name', 'Error')}")
    
    # Schumann Resonance
    logger.info("   Getting Schumann Resonance...")
    try:
        schumann_data = get_schumann_resonance() # Assumes this function is defined/imported
        chart['earth_energies']['schumann'] = schumann_data
        logger.info(f"         Schumann Resonance: {schumann_data.get('frequency')} Hz (Source: {schumann_data.get('source')})")
    except Exception as e:
        logger.error(f"Error getting Schumann resonance: {e}", exc_info=True)
        chart['earth_energies']['schumann'] = {"frequency": None, "source": "error"}

    # Parts of Fortune and Spirit
    logger.info("   Calculating Parts of Fortune and Spirit...")
    try:
        asc_deg = chart['angles'].get('Ascendant', {}).get('degree')
        sun_deg = chart['positions'].get('Sun', {}).get('degree')
        moon_deg = chart['positions'].get('Moon', {}).get('degree')
        
        pof_sign, pof_exact, pof_house, pof_degree = "Error", 0.0, 0, None
        pos_sign, pos_exact, pos_house, pos_degree = "Error", 0.0, 0, None

        if asc_deg is not None and sun_deg is not None and moon_deg is not None:
            # Determine if chart is Diurnal (Sun above horizon) or Nocturnal (Sun below horizon)
            # Horizon is Ascendant-Descendant axis. Houses 7-12 are above horizon.
            sun_house = chart['positions'].get('Sun', {}).get('house', 0) # Get Sun's house
            desc_deg = chart['angles'].get('DC',{}).get('degree') # For more precise check if needed

            is_diurnal = False
            if asc_deg is not None and desc_deg is not None: # Use direct angle comparison if possible
                # Check if Sun's longitude is between Asc and Desc (longitudinally, above horizon)
                # This is complex due to circular math. Simpler way is house position.
                if sun_house != 0 and 7 <= sun_house <= 12: # Sun in houses 7-12 is above horizon
                    is_diurnal = True
                elif sun_house != 0 and 1 <= sun_house <= 6: # Sun in houses 1-6 is below horizon
                    is_diurnal = False
                else: # Fallback if house is 0 or Error
                    logger.warning("Cannot reliably determine Diurnal/Nocturnal status for Parts calculation using Sun house. Using approximate check.")
                    # Approximate: if Sun is between Asc and Desc going counter-clockwise from Asc
                    if asc_deg < desc_deg: # Normal order
                        is_diurnal = (sun_deg > asc_deg and sun_deg < desc_deg)
                    else: # Wraps around 0 Aries (e.g. Asc 330, Desc 150)
                        is_diurnal = (sun_deg > asc_deg or sun_deg < desc_deg)
            elif sun_house != 0: # Fallback to just house check if angles are problematic
                is_diurnal = (7 <= sun_house <= 12)
            else:
                logger.warning("Cannot determine Diurnal/Nocturnal status for Parts calculation.")
            
            if is_diurnal: # Day chart
                pof_degree = (asc_deg + moon_deg - sun_deg) % 360.0
                pos_degree = (asc_deg + sun_deg - moon_deg) % 360.0
            else: # Night chart
                pof_degree = (asc_deg + sun_deg - moon_deg) % 360.0
                pos_degree = (asc_deg + moon_deg - sun_deg) % 360.0
            
            if pof_degree < 0: pof_degree += 360.0
            if pos_degree < 0: pos_degree += 360.0

            pof_sign, pof_exact = get_zodiac_sign(pof_degree)
            pos_sign, pos_exact = get_zodiac_sign(pos_degree)
            if pof_sign != 'Error': pof_house = calculate_house(pof_degree, chart['house_info']['cusps'])
            if pos_sign != 'Error': pos_house = calculate_house(pos_degree, chart['house_info']['cusps'])

            logger.debug(f"         Part of Fortune: {pof_sign} {pof_exact:.4f}°, House {pof_house} (Diurnal: {is_diurnal})")
            logger.debug(f"         Part of Spirit: {pos_sign} {pos_exact:.4f}°, House {pos_house} (Diurnal: {is_diurnal})")
        else:
            logger.warning("Part of Fortune/Spirit calculation skipped: Asc/Sun/Moon degree missing.")
            # Ensure error values are set
            pof_degree, pos_degree = None, None 

        chart['other_points']['Part of Fortune'] = {'degree': pof_degree, 'sign': pof_sign, 'exact_degree': pof_exact, 'house': pof_house}
        chart['other_points']['Part of Spirit'] = {'degree': pos_degree, 'sign': pos_sign, 'exact_degree': pos_exact, 'house': pos_house}
        # Also add to main positions dict for aspecting
        chart['positions']['Part of Fortune'] = chart['other_points']['Part of Fortune']
        chart['positions']['Part of Spirit'] = chart['other_points']['Part of Spirit']
        logger.info("         Parts of Fortune/Spirit calculation complete.")
    except Exception as e:
        logger.error(f"Error calculating Parts of Fortune/Spirit: {e}", exc_info=True)
        chart['other_points']['Part of Fortune'] = {'degree': None, 'sign': 'Error', 'exact_degree': 0.0, 'house': 0}
        chart['other_points']['Part of Spirit'] = {'degree': None, 'sign': 'Error', 'exact_degree': 0.0, 'house': 0}


    # Calculate Midpoints
    logger.info("   Calculating Midpoints...")
    calculated_midpoints = {}
    try:
        # Use only points that have valid degree and sign from chart['positions']
        valid_positions_for_midpoints = {
            p_name: data['degree'] 
            for p_name, data in chart['positions'].items() 
            if isinstance(data, dict) and data.get('degree') is not None and data.get('sign') != 'Error'
        }

        for p1_name, p2_name in MIDPOINTS_TO_CALCULATE: # Use predefined list of pairs
            mp_key = f"{p1_name}/{p2_name}"
            deg1 = valid_positions_for_midpoints.get(p1_name)
            deg2 = valid_positions_for_midpoints.get(p2_name)
            
            mp_sign, mp_exact, mp_house, mp_degree = "Error", 0.0, 0, None # Defaults

            if deg1 is not None and deg2 is not None:
                mp_degree = calculate_midpoint(deg1, deg2)
                if mp_degree is not None:
                    mp_sign, mp_exact = get_zodiac_sign(mp_degree)
                    if mp_sign != 'Error':
                        mp_house = calculate_house(mp_degree, chart['house_info']['cusps'])
                    logger.debug(f"         Midpoint {mp_key}: {mp_sign} {mp_exact:.4f}°, House {mp_house}")
                else:
                    logger.warning(f"Midpoint calculation returned None for {mp_key}.")
            else:
                logger.debug(f"Skipping midpoint {mp_key}: One or both points missing/invalid in valid_positions list.")
            
            calculated_midpoints[mp_key] = {'degree': mp_degree, 'sign': mp_sign, 'exact_degree': mp_exact, 'house': mp_house}
        chart['midpoints'] = calculated_midpoints
        logger.info(f"   Midpoint calculation finished. Calculated {len(calculated_midpoints)} midpoints.")
    except Exception as e:
        logger.error(f"Error calculating midpoints: {e}", exc_info=True)
        chart['midpoints'] = {} # Ensure it's an empty dict on error


    # Future Transits (placeholder/simplified for now)
    logger.info("   Calculating current transit positions (Placeholder)..."); chart['transits_current'] = {}; # Placeholder
    if jd_ut is None:
        logger.error("Cannot calculate Future Transits because Julian Day (jd_ut) is not valid.")
        chart['future_transits'] = []
    else:
        logger.info("   Calculating Future Transits (approx. 12 months)...")
        future_transit_events = []
        try:
            start_transit_date = calculation_start_utc.date() # Date of chart calculation
            future_transit_events = calculate_future_transits(
                natal_positions=chart['positions'],
                jd_ut_natal=jd_ut, # Natal JD_UT
                start_date=start_transit_date,
                duration_months=12, # Look ahead 12 months
                aspects_defs=MAJOR_TRANSIT_ASPECTS, # Define which aspects to track
                orb=1.5, # Orb for transit aspects
                step_days=1 # Check daily
            )
            chart['future_transits'] = future_transit_events
            logger.info(f"         Future transit calculation complete: Found {len(future_transit_events)} events.")
        except ImportError: # If dateutil.relativedelta is not available
            logger.warning("Future transits skipped: 'python-dateutil' library not found. Please install it (`pip install python-dateutil`).")
            chart['future_transits'] = []
        except Exception as e:
            logger.error(f"Error calculating future transits: {e}", exc_info=True)
            chart['future_transits'] = []


    # Fixed Star Conjunctions
    if skip_fixed_stars:
        logger.info("   Skipping fixed-star calculations as requested (skip_fixed_stars=True).")
        chart['fixed_star_links'] = []
    else:
        if jd_ut is None:
            logger.error("   Cannot calculate Fixed Stars because Julian Day (jd_ut) is not valid.")
            chart['fixed_star_links'] = []
        else:
            logger.info("   Calculating Fixed Star Conjunctions (V2 with House)…")
            fixed_star_matches = []
            try:
                # Prepare dict of {planet_name: absolute_degree} for fixed star function
                planet_positions_abs_deg_for_fs = {
                    name: data['degree']
                    for name, data in chart['positions'].items()
                    if isinstance(data, dict) and data.get('degree') is not None and data.get('sign') not in [None, 'Error']
                } # Include angles if they are in chart['positions'] and you want to check stars to them
                
                if planet_positions_abs_deg_for_fs:
                    logger.debug(f"         Calling calculate_fixed_star_conjunctions_v2 for {len(planet_positions_abs_deg_for_fs)} points...")
                    fixed_star_matches = calculate_fixed_star_conjunctions_v2(
                        planet_positions_abs_deg=planet_positions_abs_deg_for_fs,
                        house_cusps=chart['house_info']['cusps'], # Pass calculated house cusps
                        jd_ut=jd_ut, # Pass natal Julian Day
                        star_names=DEFAULT_FIXED_STAR_NAMES, # Use loaded star names
                        orb=FIXED_STAR_ORB # Use defined orb
                    )
                    logger.info(f"         Fixed Star calculation complete. Found {len(fixed_star_matches)} conjunctions.")
                else:
                    logger.warning("   No valid planet positions found to calculate fixed star conjunctions.")
                    fixed_star_matches = []
                chart['fixed_star_links'] = fixed_star_matches
            except Exception as e_fs:
                logger.error(f"   Error during fixed star conjunction calculation: {e_fs}", exc_info=True)
                chart['fixed_star_links'] = []

    # Determine Current Transit Phase (based on age and major outer planet transits)
    logger.info("   Determining Current Transit Phase...")
    phase_description = "Error" # Default
    transit_phase_orb_setting = 2.0 # Orb for checking current transits
    current_age_val = chart['birth_details'].get('age', -1) # Get calculated age
    try:
        if isinstance(current_age_val, int) and current_age_val >= 0:
            phase_description = get_current_transit_phase(current_age_val, chart['positions'], orb=transit_phase_orb_setting)
        else:
            phase_description = "Unknown (Age Error)"
            logger.warning("Could not determine transit phase due to age calculation error.")
        chart['current_transit_phase'] = phase_description
        logger.info(f"         Current Transit Phase (Age {current_age_val if isinstance(current_age_val, int) else '?'}, Orb {transit_phase_orb_setting}°): {phase_description}")
    except Exception as e:
        logger.error(f"Error determining current transit phase: {e}", exc_info=True)
        chart['current_transit_phase'] = "Error"


    calculation_end_utc = datetime.now(timezone.utc)
    duration = calculation_end_utc - calculation_start_utc
    logger.info(f"--- Chart Calculation Complete (V{__version__}) ---")
    logger.info(f"--- Duration: {duration} ---")
    return chart


def calculate_pet_chart(**kwargs):
    """Wrapper for calculate_chart that forces skip_fixed_stars=True."""
    logger.info("--- Using calculate_pet_chart wrapper ---")
    kwargs['skip_fixed_stars'] = True # Pets usually don't need fixed stars
    kwargs['gender'] = kwargs.get('gender', 'U') # Default gender to Unknown for pets if not specified

    # Convert birth_date and birth_time to year, month, day, hour, minute if provided
    if 'birth_date' in kwargs and 'birth_time' in kwargs:
        try:
            dt_obj = datetime.strptime(f"{kwargs['birth_date']} {kwargs['birth_time']}", "%Y-%m-%d %H:%M")
            kwargs['year'] = dt_obj.year
            kwargs['month'] = dt_obj.month
            kwargs['day'] = dt_obj.day
            kwargs['hour'] = dt_obj.hour
            kwargs['minute'] = dt_obj.minute
        except Exception as e:
            logger.warning(f"Could not parse birth_date/time for pet in calculate_pet_chart: {e}")
            # Allow to proceed if year, month, day, etc. are directly provided as fallback

    # Map common alternative arg names to what calculate_chart expects
    if 'latitude' in kwargs:
        kwargs['lat'] = kwargs.pop('latitude')
    if 'longitude' in kwargs:
        kwargs['lng'] = kwargs.pop('longitude')
    if 'country_code' in kwargs: # Assuming 'country' is the target key
        kwargs['country'] = kwargs.pop('country_code')
        
    # Filter kwargs to only those accepted by calculate_chart
    accepted_params = {
        'year','month','day','hour','minute',
        'lat','lng','city','country','tz_str',
        'gender','ephemeris_path_used','skip_fixed_stars',
        'full_name','house_system'
    }
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in accepted_params}
    
    dropped_params = set(kwargs.keys()) - set(filtered_kwargs.keys())
    if dropped_params:
        logger.debug(f"calculate_pet_chart: Dropped unexpected arguments: {dropped_params}")
        
    return calculate_chart(**filtered_kwargs)


if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format='%(asctime)s - %(levelname)s - CALC-TEST - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', force=True)
    logger.setLevel(logging.DEBUG) # Set to DEBUG for detailed output during testing
    logger.info(f"--- Testing advanced_calculate_astrology.py Directly (V{__version__}) ---")

    # Ephemeris Path Setup for __main__
    ephe_dir = None
    DEFAULT_EPHE_PATH_MAIN = r"C:\Users\danie\OneDrive\swisseph" # Example, adjust if needed
    
    try:
        ephe_path_from_env = os.getenv('SWEPHE_PATH')
        script_dir_path_main = None
        # Determine script_dir_path robustly
        try: 
            script_dir_path_main = os.path.dirname(os.path.abspath(__file__))
        except NameError: 
            logger.warning("__file__ not defined, attempting relative path from current directory for ephe test.")
            script_dir_path_main = os.getcwd()
        
        relative_ephe_path_main = os.path.join(script_dir_path_main, 'ephe') if script_dir_path_main else None

        if ephe_path_from_env and os.path.isdir(ephe_path_from_env):
            ephe_dir = ephe_path_from_env
            logger.info(f"Using SWEPHE_PATH environment variable: {ephe_dir}")
        elif os.path.isdir(DEFAULT_EPHE_PATH_MAIN):
            ephe_dir = DEFAULT_EPHE_PATH_MAIN
            logger.info(f"Using default ephe path (hardcoded in __main__): {ephe_dir}")
        elif relative_ephe_path_main and os.path.isdir(relative_ephe_path_main):
            ephe_dir = relative_ephe_path_main
            logger.info(f"Using relative path from script location ('ephe' subdir): {ephe_dir}")
        else:
            logger.critical("Ephemeris path not found. Set SWEPHE_PATH, update default, or place 'ephe' directory.")
            raise FileNotFoundError("Ephemeris path not found for __main__ test execution.")
        
        # Set path for this test run; calculate_chart will also set it if ephemeris_path_used is passed.
        # swe.set_ephe_path(ephe_dir) # This is redundant if calculate_chart handles it.
        # logger.info(f"Swisseph version found: {swe.version()}") # Check version

        # Test Data
        birth_info_test_main = {
            'year': 1990, 'month': 6, 'day': 15, 'hour': 14, 'minute': 30,
            'lat': 40.7128, 'lng': -74.0060, 'city': "New York", 'country': "USA",
            'tz_str': "America/New_York", 'gender': "Female", 'house_system': b'P', # Placidus
            'full_name': "Alice Test Example"
        }

        try:
            logger.info("\n--- TESTING HUMAN CHART (Fixed Stars Enabled by Default in calculate_chart unless skipped) ---")
            # Pass ephe_dir to ephemeris_path_used
            test_chart_human = calculate_chart(**birth_info_test_main, ephemeris_path_used=ephe_dir, skip_fixed_stars=False)
            
            if isinstance(test_chart_human, dict) and "error" not in test_chart_human:
                logger.info("\n--- Human Chart Results ---")
                logger.info(f"  Human Chart - Dominant Element: {test_chart_human.get('chart_signatures', {}).get('dominant_element')}")
                logger.info(f"  Human Chart - Prompt Dom1: {test_chart_human.get('chart_signatures', {}).get('prompt_dominant_element_1')}")
                logger.info(f"  Human Chart - Prompt Dom2: {test_chart_human.get('chart_signatures', {}).get('prompt_dominant_element_2')}")
                logger.info(f"  Human Chart - Prompt Least: {test_chart_human.get('chart_signatures', {}).get('prompt_least_represented_element')}")
                logger.info(f"  Human Chart - Elemental Balance %: {test_chart_human.get('elemental_balance')}")
                fixed_stars = test_chart_human.get('fixed_star_links',[])
                logger.info(f"  Fixed Stars Calculated: {len(fixed_stars)} stars linked.")
                if fixed_stars:
                    first_link = fixed_stars[0]
                    logger.info(f"    Example Link: {first_link.get('linked_planet','?')} conjunct {first_link.get('star','?')} (Orb: {first_link.get('orb','?')})")
            elif isinstance(test_chart_human, dict): # Error case
                logger.error(f"--- Human Chart Calculation Failed: {test_chart_human['error']} ---")
            else: # Unexpected return
                logger.error(f"--- Human Chart Calculation returned unexpected type: {type(test_chart_human)} ---")

            logger.info("\n--- TESTING PET CHART (Fixed Stars Skipped via calculate_pet_chart wrapper) ---")
            birth_info_pet_main = birth_info_test_main.copy() # Create a copy
            birth_info_pet_main['full_name'] = "Buddy Test Pet"
            birth_info_pet_main['gender'] = 'U' # Typically Unknown for pets
            # calculate_pet_chart will set skip_fixed_stars=True
            test_chart_pet = calculate_pet_chart(**birth_info_pet_main, ephemeris_path_used=ephe_dir)
            
            if isinstance(test_chart_pet, dict) and "error" not in test_chart_pet:
                logger.info("\n--- Pet Chart Results ---")
                logger.info(f"  Pet Chart - Dominant Element: {test_chart_pet.get('chart_signatures', {}).get('dominant_element')}")
                logger.info(f"  Pet Chart - Prompt Dom1: {test_chart_pet.get('chart_signatures', {}).get('prompt_dominant_element_1')}")
                logger.info(f"  Pet Chart - Prompt Dom2: {test_chart_pet.get('chart_signatures', {}).get('prompt_dominant_element_2')}")
                logger.info(f"  Pet Chart - Prompt Least: {test_chart_pet.get('chart_signatures', {}).get('prompt_least_represented_element')}")
                logger.info(f"  Pet Chart - Elemental Balance %: {test_chart_pet.get('elemental_balance')}")
                logger.info(f"  Fixed Stars Calculated: {len(test_chart_pet.get('fixed_star_links',[]))} stars linked. (Should be 0 for pet chart)")
            elif isinstance(test_chart_pet, dict):
                logger.error(f"--- Pet Chart Calculation Failed: {test_chart_pet['error']} ---")
            else:
                 logger.error(f"--- Pet Chart Calculation returned unexpected type: {type(test_chart_pet)} ---")

        except ValueError as val_err: # Catch specific errors like timezone issues
            logger.critical(f"Chart calculation failed due to ValueError (likely timezone or date/time parse): {val_err}", exc_info=False)
        except RuntimeError as run_err: # Catch errors raised from within calculate_chart
             logger.critical(f"Chart calculation failed due to RuntimeError: {run_err}", exc_info=False)
        except Exception as calc_err: # General catch-all for other unexpected errors
            logger.critical(f"Error during chart calculation/printing in __main__: {calc_err}", exc_info=True)
            
    except FileNotFoundError as fnf_err: # For ephemeris path issues
        logger.critical(f"Setup Error: {fnf_err}")
    except ImportError as imp_err: # For missing libraries like dateutil or zoneinfo
        if 'dateutil' in str(imp_err).lower():
            logger.critical("Import Error: 'python-dateutil' required for future transits. Install it ('pip install python-dateutil').")
        elif 'zoneinfo' in str(imp_err).lower() and sys.version_info < (3,9): # Zoneinfo is built-in 3.9+
            logger.critical("Import Error: 'backports.zoneinfo' library required for Python < 3.9. Install it ('pip install backports.zoneinfo').")
        else:
            logger.critical(f"Import Error during setup: {imp_err}.")
    except Exception as setup_err: # Other setup errors
        logger.critical(f"Unexpected error in __main__ setup: {setup_err}", exc_info=True)

    logger.info("--- Calculation Test Script Complete ---")
# --- END OF FILE advanced_calculate_astrology.py ---