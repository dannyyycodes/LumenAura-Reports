#!/usr/bin/env python3
# generate_chart_image.py
# VERSION 1.0.1 - Added filtering for None degrees in draw_planets to prevent TypeError.

import json
import math
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager
import logging # Added for logging

# --- Logger Setup ---
logger = logging.getLogger(__name__)
# Basic configuration if no handlers are set (e.g., when run standalone)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - CHART_GEN - %(message)s')


# --- Constants ---
ZODIAC_SIGNS = {
    "Aries": {"symbol": "♈", "start_deg": 0},
    "Taurus": {"symbol": "♉", "start_deg": 30},
    "Gemini": {"symbol": "♊", "start_deg": 60},
    "Cancer": {"symbol": "♋", "start_deg": 90},
    "Leo": {"symbol": "♌", "start_deg": 120},
    "Virgo": {"symbol": "♍", "start_deg": 150},
    "Libra": {"symbol": "♎", "start_deg": 180},
    "Scorpio": {"symbol": "♏", "start_deg": 210},
    "Sagittarius": {"symbol": "♐", "start_deg": 240},
    "Capricorn": {"symbol": "♑", "start_deg": 270},
    "Aquarius": {"symbol": "♒", "start_deg": 300},
    "Pisces": {"symbol": "♓", "start_deg": 330}
}

# Standard Unicode symbols for planets
PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
    "Ascendant": "ASC", "Midheaven": "MC",
    "North Node": "☊", "South Node": "☋", # Common astrological points
    "Chiron": "⚷", # Using a common Chiron symbol
    "Lilith": "Lilith", # True Black Moon Lilith
    "Fortune": "⊗", # Part of Fortune symbol (circled X)
    # Default to name if symbol not found, or first 3 letters
}

DEFAULT_CHART_STYLE = {
    "fig_size": (12, 12), # Inches
    "dpi": 300,
    "bg_color": "white",
    "zodiac_band_color": "#f0f0f0", # Light grey for zodiac band
    "zodiac_line_color": "grey",
    "sign_text_color": "black",
    "sign_font_size": 12,
    "house_line_color": "darkgrey",
    "house_number_color": "grey",
    "house_number_font_size": 8,
    "planet_text_color": "black",
    "asc_mc_text_color": "red", # Special color for Asc/MC labels
    "planet_font_size": 9,
    "planet_symbol_font_size": 12, # For text based symbols
    "planet_label_group_separation_deg": 12, # Degrees to consider planets "close" for staggering
    "font_family": "DejaVu Sans", # Good for Unicode symbols
    # Radii (relative to max radius of 1.0)
    "r_zodiac_text": 0.94,
    "r_zodiac_band_inner": 0.88,
    "r_zodiac_band_outer": 1.0,
    "r_house_lines_outer": 0.87,
    "r_house_lines_inner": 0.15, # Small gap in the center
    "r_house_number": 0.82,
    "r_planet_label_default": 0.70,
    "r_planet_label_stagger_step": 0.07, # Radial offset for staggered labels
    "max_staggered_planets_per_group": 5 # Max planets in a tight visual group to stagger
}

# --- Helper Functions ---
def degree_to_radian(degree):
    """Convert degrees to radians."""
    return np.deg2rad(degree)

def get_planet_label(name, data, style):
    """Generates the text label for a planet."""
    symbol = PLANET_SYMBOLS.get(name, name[:3]) # Use symbol or first 3 letters
    degree_val = data.get('degree') # Get degree, could be None
    
    # Ensure degree_val is a number before formatting
    if isinstance(degree_val, (int, float)):
        degree_display = f"{degree_val:.1f}°"
    else:
        degree_display = "[?]" # Placeholder for invalid degree

    # Optional: Add sign symbol to label
    sign_at_degree_symbol = ""
    if isinstance(degree_val, (int, float)): # Only attempt if degree is valid
        for sign_name_iter, sign_info_iter in ZODIAC_SIGNS.items():
            start_deg = sign_info_iter['start_deg']
            end_deg = (start_deg + 30)
            # Check if degree falls within this sign's 30-degree segment
            # Handle wrap-around for Pisces (330-360) and Aries (0-30)
            if start_deg <= degree_val < end_deg:
                sign_at_degree_symbol = ZODIAC_SIGNS[sign_name_iter]["symbol"]
                break
            elif start_deg == 330 and (degree_val >= 330 or degree_val < 0): # Pisces handling edge case
                 # This case might be complex if degrees are not 0-360 normalized earlier
                 # For now, a simple check. This part may need more robust logic if degrees aren't consistently 0-359.999
                 pass # Covered by the general loop assuming degree_val is 0-359.99

    return f"{symbol} {degree_display} {sign_at_degree_symbol}"


# --- Drawing Functions ---
def draw_zodiac_ring(ax, style):
    """Draws the outer zodiac ring with signs and symbols."""
    for sign_name, sign_data in ZODIAC_SIGNS.items():
        start_deg = sign_data["start_deg"]
        # end_deg = (start_deg + 30) % 360 # Not used in this version of plotting
        mid_deg = start_deg + 15

        # Plot sign symbol/name
        rad = degree_to_radian(mid_deg)
        ax.text(rad, style["r_zodiac_text"], sign_data["symbol"],
                ha='center', va='center', fontsize=style["sign_font_size"],
                color=style["sign_text_color"], fontfamily=style["font_family"],
                rotation = (mid_deg - 90) if (90 < mid_deg < 270) else (mid_deg + 90) # Keep text upright
               )

        # Draw dividing lines for zodiac segments
        line_rad_start = degree_to_radian(start_deg)
        ax.plot([line_rad_start, line_rad_start],
                [style["r_zodiac_band_inner"], style["r_zodiac_band_outer"]],
                color=style["zodiac_line_color"], lw=1)

    # Draw the circles that form the band
    circle_inner = plt.Circle((0, 0), style["r_zodiac_band_inner"], transform=ax.transData._b,
                              color=style["zodiac_band_color"], ec=style["zodiac_line_color"], fill=True, zorder=-10) 
    circle_outer_edge = plt.Circle((0, 0), style["r_zodiac_band_outer"], transform=ax.transData._b,
                                   color='none', ec=style["zodiac_line_color"], fill=False, lw=1.5)
    ax.add_artist(circle_inner)
    ax.add_artist(circle_outer_edge)


def draw_house_cusps(ax, house_cusps, style):
    """Draws the house cusp lines."""
    if not house_cusps or not all(isinstance(c, (int, float)) for c in house_cusps):
        logger.warning("House cusps data invalid or missing. Skipping drawing house cusps.")
        return

    for cusp_deg in house_cusps:
        rad = degree_to_radian(cusp_deg)
        ax.plot([rad, rad], [style["r_house_lines_inner"], style["r_house_lines_outer"]],
                color=style["house_line_color"], linestyle='-', lw=1)

def draw_house_numbers(ax, house_cusps, style):
    """Draws house numbers in the middle of each house sector."""
    if not house_cusps or not all(isinstance(c, (int, float)) for c in house_cusps) or len(house_cusps) != 12:
        logger.warning("House cusps data invalid or incomplete for drawing numbers. Skipping.")
        return

    num_cusps = len(house_cusps)
    for i in range(num_cusps):
        cusp1_deg = house_cusps[i]
        cusp2_deg = house_cusps[(i + 1) % num_cusps]
        
        mid_deg = 0
        # Calculate midpoint angle, handling wrap-around 360 degrees
        if cusp2_deg < cusp1_deg: # e.g. cusp1 = 350 (House 12), cusp2 = 10 (House 1)
            # Arc crosses 0 degrees Aries
            mid_deg = (cusp1_deg + (360 + cusp2_deg - cusp1_deg) / 2.0) % 360
        else:
            mid_deg = (cusp1_deg + cusp2_deg) / 2.0
        mid_deg %= 360 # Ensure it's within 0-360

        rad = degree_to_radian(mid_deg)
        house_num_str = str(i + 1)

        text_rotation = mid_deg - 90
        if 90 < mid_deg < 270: 
             text_rotation = mid_deg + 90

        ax.text(rad, style["r_house_number"], house_num_str,
                ha='center', va='center', fontsize=style["house_number_font_size"],
                color=style["house_number_color"], fontfamily=style["font_family"],
                rotation=text_rotation
                )

def draw_planets(ax, positions, style):
    """Draws planets on the chart, attempting to avoid label overlap."""
    if not positions:
        logger.warning("No planet positions data provided. Skipping drawing planets.")
        return

    # --- PATCH: Filter out planets/points with None or invalid degrees BEFORE sorting ---
    valid_positions = {}
    for name, data in positions.items():
        if isinstance(data, dict) and isinstance(data.get('degree'), (int, float)):
            valid_positions[name] = data
        else:
            logger.warning(f"Skipping planet {name} due to missing or invalid degree: {data.get('degree')}")
    
    if not valid_positions:
        logger.warning("No valid planet positions to draw after filtering.")
        return
    # --- END OF PATCH ---

    # Sort planets by degree to handle groups for staggering
    sorted_planet_items = sorted(valid_positions.items(), key=lambda item: item[1]['degree'])
    
    plotted_planets_info = [] 

    # Group close planets
    planet_groups = []
    current_group = []
    for i, (name, data) in enumerate(sorted_planet_items):
        if not current_group:
            current_group.append((name, data))
        else:
            prev_deg = current_group[-1][1]['degree']
            current_deg = data['degree']
            diff = abs(current_deg - prev_deg)
            angular_dist = min(diff, 360 - diff)

            if angular_dist < style["planet_label_group_separation_deg"]:
                current_group.append((name, data))
            else:
                planet_groups.append(current_group)
                current_group = [(name, data)]
    if current_group:
        planet_groups.append(current_group)

    # Plot planets, staggering labels for close groups
    for group in planet_groups:
        num_in_group = len(group)
        # is_asc_mc_group = any(p_name in ["Ascendant", "Midheaven"] for p_name, _ in group) # Not used currently
        
        for i, (name, data) in enumerate(group):
            degree = data['degree']
            rad = degree_to_radian(degree)
            label_text = get_planet_label(name, data, style)

            r_label = style["r_planet_label_default"]
            if num_in_group > 1 and num_in_group <= style["max_staggered_planets_per_group"]:
                if i == 0: 
                    radial_idx = 0
                elif i % 2 == 1: 
                    radial_idx = - (i // 2 + 1)
                else: 
                    radial_idx = (i // 2)
                r_label = style["r_planet_label_default"] + radial_idx * style["r_planet_label_stagger_step"]

            text_color = style["asc_mc_text_color"] if name in ["Ascendant", "Midheaven"] else style["planet_text_color"]
            
            label_rotation = degree
            if 0 <= degree <= 180: 
                label_rotation = degree - 90
            else: 
                label_rotation = degree + 90
            
            if name == "Ascendant":
                ax.text(rad, style["r_house_lines_inner"] -0.01 , "ASC", ha='center', va='top', color=style["asc_mc_text_color"], fontsize=style["planet_font_size"]+1, weight='bold', fontfamily=style["font_family"])
                ax.plot([rad, rad], [0, style["r_zodiac_band_outer"]], color=style["asc_mc_text_color"], linestyle='-', lw=1.5, zorder=5)
            elif name == "Midheaven":
                ax.plot([rad, rad], [style["r_house_lines_inner"], style["r_zodiac_band_outer"]], color=style["asc_mc_text_color"], linestyle='-', lw=1.5, zorder=5)
                text_r_mc = style["r_zodiac_band_inner"] - 0.03
                va_mc = 'top'
                if 180 < degree < 360: 
                    va_mc = 'bottom'
                ax.text(rad, text_r_mc, "MC", ha='center', va=va_mc, color=style["asc_mc_text_color"], fontsize=style["planet_font_size"]+1, weight='bold', fontfamily=style["font_family"])
            else:
                 planet_text_obj = ax.text(rad, r_label, label_text,
                                ha='center', va='center', fontsize=style["planet_font_size"],
                                color=text_color, fontfamily=style["font_family"],
                                rotation=label_rotation, rotation_mode='anchor', zorder=10)
                 plotted_planets_info.append({'name': name, 'degree': degree, 'radius': r_label, 'object': planet_text_obj})


# --- Main Function ---
def generate_chart_image(positions_data, house_cusps_data, output_file, style=None):
    """
    Generates and saves the astrological chart image.
    """
    if style is None:
        style = DEFAULT_CHART_STYLE.copy() # Use a copy to avoid modifying the global default
    else: # If a partial style is passed, merge it with defaults
        temp_style = DEFAULT_CHART_STYLE.copy()
        temp_style.update(style)
        style = temp_style

    plt.rcParams['font.family'] = style["font_family"]

    fig = plt.figure(figsize=style["fig_size"])
    ax = plt.subplot(111, projection='polar')

    fig.patch.set_facecolor(style["bg_color"])
    ax.set_facecolor(style["bg_color"])

    ax.set_theta_direction(-1)
    ax.set_theta_zero_location('E')

    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['polar'].set_visible(False)

    ax.set_ylim(0, style["r_zodiac_band_outer"])

    draw_zodiac_ring(ax, style)

    if house_cusps_data:
        draw_house_cusps(ax, house_cusps_data, style)
        draw_house_numbers(ax, house_cusps_data, style)

    draw_planets(ax, positions_data, style)
    
    if style["r_house_lines_inner"] > 0:
        center_gap_circle = plt.Circle((0, 0), style["r_house_lines_inner"], transform=ax.transData._b,
                                   color=style["bg_color"], ec=style["house_line_color"], fill=True, zorder=0)
        ax.add_artist(center_gap_circle)

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        except OSError as e:
            logger.error(f"Could not create output directory '{output_dir}': {e}")
            # Fallback to current directory or raise error? For now, let savefig try.

    try:
        plt.savefig(output_file, format='png', bbox_inches='tight', dpi=style["dpi"])
        logger.info(f"Astrological chart image saved to: {output_file}")
    except Exception as e:
        logger.error(f"Error saving chart image: {e}", exc_info=True)
    finally:
        plt.close(fig)


# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Astrological Birth Chart Image for Pet Astrology Reports.")
    parser.add_argument("--positions_file", type=str, required=True,
                        help="Path to the JSON file containing celestial object positions.")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to save the generated PNG image (e.g., astro_reports_output/chart_wheel_Luna.png).")

    args = parser.parse_args()

    try:
        with open(args.positions_file, 'r') as f:
            input_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Error: Positions file not found at {args.positions_file}")
        sys.exit(1) # Use sys.exit for command-line scripts
    except json.JSONDecodeError:
        logger.error(f"Error: Could not decode JSON from {args.positions_file}")
        sys.exit(1)

    positions = input_data.get("positions")
    if not positions:
        logger.error("Error: 'positions' key not found or empty in the JSON file.")
        sys.exit(1)

    house_cusps = input_data.get("house_cusps")

    generate_chart_image(positions, house_cusps, args.output) # Will use DEFAULT_CHART_STYLE