import os
import json
import logging # Optional: Add logging if you want logs from the loader itself

# Configure logger for json_loader if desired
# json_loader_logger = logging.getLogger(__name__)
# ... (add handler and level configuration if needed) ...

# Base directory for all JSON interpretation files
# (Using the definitions you provided)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_JSON_DIR = os.path.join(SCRIPT_DIR, "Data jsons")

# Simple cache to avoid reloading JSON files repeatedly
_json_cache = {}

# <<< NEW FUNCTION ADDED BELOW >>>
def load_json_data(group: str) -> dict | None:
    """
    Loads, parses, and caches the entire JSON data for a given interpretation group.
    The 'group' name should correspond to the JSON filename root (e.g., 'house', 'planets').
    Returns the dictionary or None if loading fails.
    """
    if not group or not isinstance(group, str):
        # Use logger if configured, otherwise print
        # json_loader_logger.error("load_json_data called with invalid group name.")
        print(f"ERROR: load_json_data called with invalid group name: {group}")
        return None

    # Use a normalized key for the cache, but original group name for filename
    normalized_group_for_cache = group.lower().replace(" ", "_").replace("-", "_")

    if normalized_group_for_cache in _json_cache:
        # json_loader_logger.debug(f"Returning cached data for group: {normalized_group_for_cache}")
        # Return a copy to prevent modification of the cached object if needed,
        # but for read-only purposes, returning the direct reference is more efficient.
        return _json_cache[normalized_group_for_cache]

    # Construct filename based on the group name passed in
    # (Assumes mapping/normalization for filename happened before calling this)
    filename = f"{group}.json"
    filepath = os.path.join(DATA_JSON_DIR, filename)

    try:
        # json_loader_logger.debug(f"Attempting to load JSON data from: {filepath}")
        print(f"LOADER: Attempting to load JSON data from: {filepath}") # Using print for visibility for now
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
             # json_loader_logger.error(f"JSON data in {filepath} is not a dictionary.")
             print(f"ERROR: JSON data in {filepath} is not a dictionary.")
             _json_cache[normalized_group_for_cache] = None # Cache failure
             return None # Return None if not a dict

        # Cache the successfully loaded dictionary
        _json_cache[normalized_group_for_cache] = data
        # json_loader_logger.info(f"Successfully loaded and cached data for group: {group}")
        print(f"LOADER: Successfully loaded and cached data for group: {group}")
        return data
    except FileNotFoundError:
        # json_loader_logger.warning(f"JSON file not found: {filepath}")
        print(f"WARNING: JSON file not found: {filepath}")
        _json_cache[normalized_group_for_cache] = None # Cache the failure (None) to avoid retrying
        return None
    except json.JSONDecodeError as e:
        # json_loader_logger.error(f"Error decoding JSON from {filepath}: {e}")
        print(f"ERROR: Error decoding JSON from {filepath}: {e}")
        _json_cache[normalized_group_for_cache] = None # Cache the failure
        return None
    except Exception as e:
        # json_loader_logger.error(f"Unexpected error loading JSON from {filepath}: {e}", exc_info=True)
        print(f"ERROR: Unexpected error loading JSON from {filepath}: {e}")
        _json_cache[normalized_group_for_cache] = None # Cache the failure
        return None
# <<< END OF NEW FUNCTION >>>


# <<< EXISTING FUNCTION BELOW (Unchanged) >>>
def get_interpretation(category: str, key: str):
    """
    Load the JSON file named '{category}.json' from the Data jsons folder,
    and return the value for the given key. Raises an error if the file
    or key is missing.

    NOTE: This function performs a direct, flat key lookup and raises errors.
          The main logic now uses safe_get_interp (in the generator script)
          which calls load_json_data and handles nested lookups internally.
          This function might become redundant.
    """
    filename = f"{category}.json"
    filepath = os.path.join(DATA_JSON_DIR, filename)

    # Check if file exists first (more specific error)
    if not os.path.isfile(filepath):
        # Consider logging this instead of raising immediately depending on usage context
        # logger.error(f"Interpretation file not found: {filepath}")
        raise FileNotFoundError(f"Interpretation file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            # logger.error(f"Error decoding JSON in {filepath}: {e}")
            raise ValueError(f"Error decoding JSON in {filepath}: {e}")

    # Check if key exists in the loaded data
    if key not in data:
        # logger.error(f"Key '{key}' not found in {filename}")
        raise KeyError(f"Key '{key}' not found in {filename}")

    # Return the value for the key
    return data[key]