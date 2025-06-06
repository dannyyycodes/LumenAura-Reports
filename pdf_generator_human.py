# pdf_generator.py (This is your pdf_generator_human.py)

# --- VERSION 16.0.2 — Fix IndentationError, clean tabs/spaces ---
# --- (Assumed) VERSION 16.0.3 — Corrected _add_image method logic --- 

# --- VERSION 16.0.1 — Minor tweaks: Pet default divider width, Pet cover title fallback ---
# --- VERSION 16.0.0 — Integrated Pet Report Styling, Intros, Quotes, Dividers ---
# ... (rest of your version history) ...


import os
import re
import traceback
import hashlib
import json
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor, black, white, silver, darkgray, gold, navy # Example colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Flowable,
    PageBreak, NextPageTemplate, HRFlowable, FrameBreak, SimpleDocTemplate, KeepTogether,
    Table, TableStyle
)
from reportlab.graphics.shapes import Drawing # Keep if shapes used elsewhere
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit # Keep ImageReader import as it might be used elsewhere or was intended for other logic
import html
import logging
from collections import defaultdict
from datetime import date
import random # <-- Import random for selecting quotes


# Basic Logging Setup
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - PDFGEN:%(lineno)d - %(message)s')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)
    logger.info("PDF Generator Logger configured.")
else:
    logger.info("PDF Generator Logger already configured.")

# svglib import (Optional)
try: from svglib.svglib import svg2rlg; _svglib_available = True; logger.info("svglib found.")
except ImportError: _svglib_available = False; logger.warning("svglib not found. SVG chart handling might be limited.")

# Registered Font Names (Initialized in _register_fonts)
REGISTERED_FONT_NAMES = []

# --- Path Definitions ---
try: SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
except NameError: SCRIPT_DIR = os.getcwd(); logger.warning(f"__file__ not defined, using CWD for paths: {SCRIPT_DIR}")

ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets') # Base assets dir
DEFAULT_IMAGES_DIR = os.path.join(ASSETS_DIR, 'images') # Default images sub-directory
FONTS_DIR = os.path.join(SCRIPT_DIR, 'fonts')
DATA_JSONS_DIR = os.path.join(SCRIPT_DIR, 'Data jsons') # <-- Define Data jsons directory

logger.info(f"Assets directory expected at: {ASSETS_DIR}")
logger.info(f"Fonts directory expected at: {FONTS_DIR}")
logger.info(f"Data jsons directory expected at: {DATA_JSONS_DIR}")

# --- Occasion Styles Configuration Loading ---
OCCASION_STYLES_FILE = os.path.join(DATA_JSONS_DIR, 'occasion_styles.json')
OCCASION_STYLES = {} # Initialize as empty dict
try:
    logger.info(f"PDF Generator attempting to load occasion styles from: {OCCASION_STYLES_FILE}")
    with open(OCCASION_STYLES_FILE, 'r', encoding='utf-8') as f:
        OCCASION_STYLES = json.load(f)
    logger.info(f"PDF Generator loaded occasion styles from {OCCASION_STYLES_FILE}")
except FileNotFoundError:
    logger.warning(f"PDF Generator: Occasion styles file not found: {OCCASION_STYLES_FILE}; using defaults")
except json.JSONDecodeError as e:
    logger.error(f"PDF Generator: Error parsing {OCCASION_STYLES_FILE}: {e}; using defaults")
except Exception as e:
    logger.error(f"PDF Generator: Unexpected error loading occasion styles: {e}", exc_info=True)

# --- Pet Quotes Loading ---
PET_QUOTE_FILE = os.path.join(DATA_JSONS_DIR, 'pet_quotes.json')
PET_QUOTES = []
try:
    logger.info(f"PDF Generator attempting to load pet quotes from: {PET_QUOTE_FILE}")
    with open(PET_QUOTE_FILE, 'r', encoding='utf-8') as f:
        PET_QUOTES = json.load(f)
    if not isinstance(PET_QUOTES, list):
        logger.error(f"Pet quotes file '{PET_QUOTE_FILE}' did not load as a list. Quotes will be unavailable.")
        PET_QUOTES = []
    else:
        logger.info(f"PDF Generator loaded {len(PET_QUOTES)} pet quotes from {PET_QUOTE_FILE}")
except FileNotFoundError:
    logger.warning(f"PDF Generator: Pet quotes file not found: {PET_QUOTE_FILE}; pet quotes will be unavailable.")
except json.JSONDecodeError as e:
    logger.error(f"PDF Generator: Error parsing {PET_QUOTE_FILE}: {e}; pet quotes will be unavailable.")
except Exception as e:
    logger.error(f"PDF Generator: Unexpected error loading pet quotes: {e}", exc_info=True)

# --- Default Image Paths & Artwork ---
DEFAULT_HUMAN_COVER_IMAGE = os.path.join(DEFAULT_IMAGES_DIR, "covers", "default_cover.jpg")
DEFAULT_HUMAN_DIVIDER_IMAGE = os.path.join(DEFAULT_IMAGES_DIR, "dividers", "default_divider.png")
DEFAULT_PET_COVER_IMAGE = os.path.join(DEFAULT_IMAGES_DIR, "covers", "default_pet_cover.jpg") 
DEFAULT_PET_DIVIDER_IMAGE = os.path.join(DEFAULT_IMAGES_DIR, "dividers", "default_pet_divider.png") 

ARTWORK_PATHS = {
    "03_Earth_Energies": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "Earthenergies.jpg"),
    "04_Fixed_Stars_Constellations": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "fixedstars.jpeg"),
    "05_Core_Essence": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "coreessence.jpg"),
    "06_Elemental_Chakras": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "elementalchakra.jpeg"),
    "06b_Modality_Balance": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "modalitybalance.jpeg"),
    "07_Numerology": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "numerology.jpeg"),
    "08_Soul_Key": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "soulkey.jpeg"),
    "09_Planetary_Analysis": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "planetary analysis.jpeg"),
    "10_Celestial_Poetry": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "Flower.jpeg"),
    "11_Asteroid_Goddesses": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "asteroids.jpeg"),
    "12_Karmic_Patterns": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "Karmic.jpeg"),
    "12b_Part_of_Fortune": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "partoffortune.jpeg"),
    "13_Career_Wealth": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "careerwealth.jpeg"),
    "14_Love_Soulmates": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "Love, Soulmates & Twin Flames.jpeg"),
    "15_Archetypes": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "archetypes.jpeg"),
    "16_Sensory_Signature": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "sensorysignature.jpeg"),
    "17_Quantum_Timelines": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "quantum possibilities.jpeg"),
    "18_Quantum_Mirror": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "quantum mirror.jpeg"),
    "19_Transits_Forecasts": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "transitsandforecasts.jpeg"),
    "20_Spiritual_Awakening": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "spiritual awakening.jpeg"),
    "21_Personalized_Guidance": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "cosmicguidance.jpeg"),
    "22_Final_Message": os.path.join(DEFAULT_IMAGES_DIR, "artwork", "finalmessage.jpeg"),
    "stonehenge_image": os.path.join(DEFAULT_IMAGES_DIR, "misc", "stonehenge.jpg"),
    "pyramid_image": os.path.join(DEFAULT_IMAGES_DIR, "misc", "pyramid.jpg"),
}

STATIC_INTROS_PET = {
    "01_Mythic_Prologue": "Every pet's journey begins with a cosmic bark or meow, a little soul sign written in the stars. Let's sniff out the secrets of {client_name}'s celestial origins!",
}

COLOR_HUMAN_BG = HexColor("#0B132B"); COLOR_HUMAN_PAGE_BORDER = silver
COLOR_HUMAN_DIVIDER = silver; COLOR_HUMAN_BODY_TEXT = white
COLOR_HUMAN_H1_TITLE = HexColor("#FFD700"); COLOR_HUMAN_H3_SUBHEAD = silver
COLOR_HUMAN_H4_SUBHEAD = silver; COLOR_HUMAN_INLINE_QUOTE_TEXT = white
COLOR_HUMAN_HEADER_QUOTE = silver; COLOR_HUMAN_CAPTION_TEXT = silver
COLOR_HUMAN_TABLE_TEXT = white; COLOR_HUMAN_TABLE_HEADER = gold
COLOR_HUMAN_TABLE_GRID = silver; COLOR_HUMAN_CLIENT_TABLE_HEADER_BG = HexColor("#1E2A47")
COLOR_HUMAN_CLIENT_TABLE_GRID = HexColor("#4A4E69"); COLOR_HUMAN_CLIENT_TABLE_TEXT = white
COLOR_HUMAN_CLIENT_TABLE_FEATURE_TEXT = gold

COLOR_PET_BG = HexColor("#FFFFFF"); COLOR_PET_PAGE_BORDER = HexColor("#00BFA6")
COLOR_PET_DIVIDER_HR = HexColor("#FF6F3C"); COLOR_PET_BODY_TEXT = HexColor("#333333")
COLOR_PET_HIGHLIGHT_BG = HexColor("#FFD54F"); COLOR_PET_HIGHLIGHT_TEXT = HexColor("#333333")
COLOR_PET_H1_TITLE = HexColor("#00BFA6"); COLOR_PET_H3_SUBHEAD = HexColor("#FF6F3C")
COLOR_PET_H4_SUBHEAD = HexColor("#333333"); COLOR_PET_TABLE_TEXT = HexColor("#333333")
COLOR_PET_TABLE_HEADER = HexColor("#00BFA6"); COLOR_PET_TABLE_GRID = HexColor("#FF6F3C")
COLOR_PET_CLIENT_TABLE_HEADER_BG = HexColor("#E0E0E0"); COLOR_PET_CLIENT_TABLE_GRID = HexColor("#FF6F3C")
COLOR_PET_CLIENT_TABLE_TEXT = HexColor("#333333"); COLOR_PET_CLIENT_TABLE_FEATURE_TEXT = HexColor("#00BFA6")

pdf_generator_version_marker = "16.0.3" # Updated version to reflect _add_image fix

def page_decorator(canvas, doc):
    canvas.saveState(); page_width, page_height = doc.pagesize
    is_pet_report = getattr(doc, 'is_pet_report', False)
    
    # Use attributes directly from the doc object if set by the builder (e.g., PetPDFBuilder)
    bg_color_override = getattr(doc, 'theme_bg_color', None)
    border_color_override = getattr(doc, 'theme_border_color', None)
    background_image_path_override = getattr(doc, 'theme_background_image_path', 'USE_DEFAULT_HUMAN_IF_NONE_SPECIFIED') # Special marker

    final_bg_color = None
    final_border_color = None
    drawn_background_image = False

    if is_pet_report:
        final_bg_color = bg_color_override if bg_color_override is not None else COLOR_PET_BG
        final_border_color = border_color_override if border_color_override is not None else COLOR_PET_PAGE_BORDER
        # Pets generally don't have a background image in this setup
        if background_image_path_override not in [None, 'USE_DEFAULT_HUMAN_IF_NONE_SPECIFIED'] and os.path.exists(background_image_path_override):
            try:
                canvas.drawImage(background_image_path_override, 0, 0, width=page_width, height=page_height, preserveAspectRatio=False, anchor='c', mask='auto')
                drawn_background_image = True
            except Exception as bg_err: logger.error(f"Error drawing OVERRIDDEN pet background image: {bg_err}.", exc_info=False)
    else: # Human report
        final_border_color = border_color_override if border_color_override is not None else COLOR_HUMAN_PAGE_BORDER
        human_default_bg_image_path = os.path.join(ASSETS_DIR, "Background.jpg")
        
        path_to_try_for_human_bg = human_default_bg_image_path
        if background_image_path_override not in [None, 'USE_DEFAULT_HUMAN_IF_NONE_SPECIFIED']:
            path_to_try_for_human_bg = background_image_path_override # Use override if valid

        if os.path.exists(path_to_try_for_human_bg):
            try:
                canvas.drawImage(path_to_try_for_human_bg, 0, 0, width=page_width, height=page_height, preserveAspectRatio=False, anchor='c', mask='auto')
                drawn_background_image = True
            except Exception as bg_err: logger.error(f"Error drawing human background image from '{path_to_try_for_human_bg}': {bg_err}.", exc_info=False)
        else:
            logger.warning(f"Human background image not found at '{path_to_try_for_human_bg}', using fallback color.")
        
        if not drawn_background_image: # Fallback to color if image failed or wasn't specified for override
            final_bg_color = bg_color_override if bg_color_override is not None else COLOR_HUMAN_BG

    if final_bg_color and not drawn_background_image: # Only fill if no image was drawn
        canvas.setFillColor(final_bg_color); canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    
    if final_border_color: # Check if a border color is set
      canvas.setStrokeColor(final_border_color); canvas.setLineWidth(0.5); canvas.rect(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, fill=0, stroke=1)
    
    canvas.restoreState()

class DejaVuPDFBuilder:
    def __init__(self, output_path, generation_context):
        self.output_path = output_path
        self.context = generation_context
        self.critical_fonts_missing = False
        self.missing_assets = []
        self.sections = self.context.get('sections', {})
        self.client_name = self.context.get('client_name', 'Valued Client')
        self.chart_data = self.context.get('chart_data', {})
        self.chart_image_path = self.context.get('chart_image_path')
        self.PROMPTS_TO_USE = self.context.get('PROMPTS_TO_USE', {})
        self.SECTION_LAYOUT_PRESETS = self.context.get('SECTION_LAYOUT_PRESETS', {})
        self.occasion_mode = self.context.get('occasion_mode', 'default')
        self.is_pet_report = self.context.get('is_pet_report', False)
        self.pet_breed = self.context.get('pet_breed')
        
        self._register_fonts()
        if self.critical_fonts_missing:
            raise RuntimeError("CRITICAL ERROR: Required fonts missing. Cannot proceed.")
        
        self.pet_quotes = PET_QUOTES
        self.current_occasion_style = OCCASION_STYLES.get(self.occasion_mode, {})
        
        # Resolve paths using ASSETS_DIR and paths from occasion_styles.json
        # This logic ensures paths from JSON are treated as relative to ASSETS_DIR if not absolute
        def resolve_from_occasion_or_default(json_key, default_human, default_pet):
            path_from_json = self.current_occasion_style.get(json_key)
            chosen_default = default_pet if self.is_pet_report else default_human
            
            final_path = chosen_default # Start with the hardcoded default for the report type
            
            if path_from_json: # If occasion_styles.json specifies a path
                if os.path.isabs(path_from_json):
                    final_path = path_from_json # Use it if absolute
                else:
                    # This is where paths like "images/covers/file.jpg" (from corrected JSON) are joined
                    final_path = os.path.abspath(os.path.join(ASSETS_DIR, path_from_json))
            
            # Log the final path being considered
            logger.debug(f"Path for '{json_key}': JSON specified '{path_from_json}', resolved to '{final_path}' (default was '{chosen_default}')")
            return final_path

        self.cover_image_path = resolve_from_occasion_or_default(
            'cover_image', DEFAULT_HUMAN_COVER_IMAGE, DEFAULT_PET_COVER_IMAGE
        )
        self.general_divider_path = resolve_from_occasion_or_default(
            'divider_image', DEFAULT_HUMAN_DIVIDER_IMAGE, DEFAULT_PET_DIVIDER_IMAGE
        )
        
        # Document theme attributes (can be overridden by subclasses like PetPDFBuilder)
        # Base values come from the loaded occasion style for the current mode.
        self.doc_theme_bg_color = HexColor(self.current_occasion_style.get('theme_color', "#FFFFFF")) if self.current_occasion_style.get('theme_color') else (COLOR_PET_BG if self.is_pet_report else COLOR_HUMAN_BG)
        self.doc_theme_border_color = HexColor(self.current_occasion_style.get('theme_color', "#000000")) if self.current_occasion_style.get('theme_color') else (COLOR_PET_PAGE_BORDER if self.is_pet_report else COLOR_HUMAN_PAGE_BORDER)
        # Background image from occasion_styles.json if specified, else None.
        _bg_img_path_json = self.current_occasion_style.get('background_image') # New optional key in JSON
        if _bg_img_path_json:
            self.doc_theme_background_image_path = os.path.abspath(os.path.join(ASSETS_DIR, _bg_img_path_json)) if not os.path.isabs(_bg_img_path_json) else _bg_img_path_json
        else:
            self.doc_theme_background_image_path = None # Default to no specific theme image from JSON


        self._check_assets() # Check after all paths are determined

        self.styles = self._create_styles()
        if 'BodyStyle' not in self.styles or 'HighlightStyle' not in self.styles:
            raise RuntimeError("CRITICAL ERROR: PDF Styles did not initialize correctly.")
        
        self.doc = BaseDocTemplate(
            output_path, pagesize=LETTER, leftMargin=0.75*inch, rightMargin=0.75*inch,
            topMargin=0.75*inch, bottomMargin=0.75*inch,
            title=f"Cosmic Blueprint for {self.client_name}",
            author="Lumen Aura / Daniel Phoenix Astrology", showBoundary=0
        )
        # Set attributes on doc for page_decorator AFTER doc is created
        self.doc.is_pet_report = self.is_pet_report
        self.doc.theme_bg_color = self.doc_theme_bg_color
        self.doc.theme_border_color = self.doc_theme_border_color
        self.doc.theme_background_image_path = self.doc_theme_background_image_path


    def _register_fonts(self):
        global REGISTERED_FONT_NAMES
        REGISTERED_FONT_NAMES = ['Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 'Helvetica-BoldOblique', 'Times-Roman', 'Times-Bold', 'Times-Italic', 'Times-BoldItalic', 'Courier', 'Courier-Bold', 'Courier-Oblique', 'Courier-BoldOblique', 'Symbol', 'ZapfDingbats']
        logger.info(f"Registering PDF fonts (DejaVu family from: {FONTS_DIR})...")
        try:
            fonts_to_register = {
                'DejaVuSans': 'DejaVuSans.ttf', 'DejaVuSans-Bold': 'DejaVuSans-Bold.ttf',
                'DejaVuSans-Oblique': 'DejaVuSans-Oblique.ttf', 'DejaVuSans-BoldOblique': 'DejaVuSans-BoldOblique.ttf',
                'DejaVuSerif': 'DejaVuSerif.ttf', 'DejaVuSerif-Bold': 'DejaVuSerif-Bold.ttf',
                'DejaVuSerif-Italic': 'DejaVuSerif-Italic.ttf', 'DejaVuSerif-BoldItalic': 'DejaVuSerif-BoldItalic.ttf'
            }
            fonts_registered_successfully = []
            if not os.path.isdir(FONTS_DIR):
                logger.error(f"Font directory not found: {FONTS_DIR}. Cannot register custom fonts.")
                self.critical_fonts_missing = True; return

            for font_name, font_filename in fonts_to_register.items():
                font_path = os.path.join(FONTS_DIR, font_filename)
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        logger.info(f"  Registered: {font_name} ({font_filename})")
                        REGISTERED_FONT_NAMES.append(font_name)
                        fonts_registered_successfully.append(font_name)
                    except Exception as e: logger.error(f"  Error registering {font_name} from {font_path}: {e}", exc_info=False)
                else:
                    logger.warning(f"  Font file not found, skipping: {font_path}")
                    if font_name in ['DejaVuSans', 'DejaVuSans-Bold']:
                        self.critical_fonts_missing = True; logger.error(f"CRITICAL Font missing: {font_name}")
            
            # Set instance attributes for direct use in _create_styles
            self.REGISTERED_FONT_NAMES = list(REGISTERED_FONT_NAMES) # Store a copy on instance
            self.sans_font = 'DejaVuSans' if 'DejaVuSans' in fonts_registered_successfully else 'Helvetica'
            self.sans_bold_font = 'DejaVuSans-Bold' if 'DejaVuSans-Bold' in fonts_registered_successfully else 'Helvetica-Bold'
            self.sans_italic_font = 'DejaVuSans-Oblique' if 'DejaVuSans-Oblique' in fonts_registered_successfully else 'Helvetica-Oblique'
            self.serif_font = 'DejaVuSerif' if 'DejaVuSerif' in fonts_registered_successfully else 'Times-Roman'
            self.serif_bold_font = 'DejaVuSerif-Bold' if 'DejaVuSerif-Bold' in fonts_registered_successfully else 'Times-Bold'


            if 'DejaVuSans' not in fonts_registered_successfully:
                logger.critical("  CRITICAL: DejaVuSans (base font) failed to register! PDF will likely fail or use default fonts.")
                self.critical_fonts_missing = True
            if 'DejaVuSerif' not in fonts_registered_successfully: logger.warning("  DejaVuSerif not registered, serif fallback may occur.")
        except Exception as e:
            logger.critical(f"CRITICAL ERROR during font registration process: {e}", exc_info=True)
            self.critical_fonts_missing = True
        finally: logger.info(f"  Font registration process finished. Available fonts for styles: {REGISTERED_FONT_NAMES}")

    def _check_assets(self):
        logger.info("Checking required image assets...")
        human_default_bg_image_path = os.path.join(ASSETS_DIR, "Background.jpg") 

        assets_to_check = {
            "Cover Image (resolved)": self.cover_image_path,
            "General Divider Image (resolved)": self.general_divider_path,
        }
        if not self.is_pet_report: # Only check human background for human reports
             assets_to_check["Human Background Image (default)"] = human_default_bg_image_path
        
        # Check theme_background_image_path if set from occasion_styles.json
        if hasattr(self, 'doc_theme_background_image_path') and self.doc_theme_background_image_path:
            assets_to_check["Theme Background Image (from Occasion)"] = self.doc_theme_background_image_path


        self.missing_assets = []
        for name, path in assets_to_check.items():
            if path and isinstance(path, (str, os.PathLike)) and not os.path.exists(path):
                log_func = logger.error if "Cover Image" in name or "Background Image" in name else logger.warning
                log_func(f"ASSET MISSING: {name} not found at expected path: {path}")
                self.missing_assets.append(f"{name} ({os.path.basename(str(path))})")
            elif path and isinstance(path, (str, os.PathLike)): logger.info(f"  Asset verified: {name} ({os.path.basename(path)})")
            elif not path: logger.debug(f"Asset not applicable or path not set for: {name}")
            else: logger.warning(f"Asset path for '{name}' is not a string or PathLike object: {path} (type: {type(path)})")


        if self.missing_assets: logger.warning(f"Some essential assets missing: {', '.join(self.missing_assets)}. Report appearance may be affected.")


    def _create_styles(self):
        logger.info("Creating PDF paragraph styles...")
        styles = getSampleStyleSheet()
        if self.is_pet_report:
            logger.info("  Using Pet Light Theme Colors.")
            body_color, h1_color, h3_color, h4_color, header_quote_color, caption_color, \
            table_text_color, table_header_color, table_grid_color, client_table_header_bg, \
            client_table_grid, client_table_text, client_table_feature_text, divider_hr_color = \
            COLOR_PET_BODY_TEXT, COLOR_PET_H1_TITLE, COLOR_PET_H3_SUBHEAD, COLOR_PET_H4_SUBHEAD, COLOR_PET_BODY_TEXT, \
            COLOR_PET_BODY_TEXT, COLOR_PET_TABLE_TEXT, COLOR_PET_TABLE_HEADER, COLOR_PET_TABLE_GRID, \
            COLOR_PET_CLIENT_TABLE_HEADER_BG, COLOR_PET_CLIENT_TABLE_GRID, COLOR_PET_CLIENT_TABLE_TEXT, \
            COLOR_PET_CLIENT_TABLE_FEATURE_TEXT, COLOR_PET_DIVIDER_HR
        else:
            logger.info("  Using Human Dark Theme Colors.")
            body_color, h1_color, h3_color, h4_color, header_quote_color, caption_color, \
            table_text_color, table_header_color, table_grid_color, client_table_header_bg, \
            client_table_grid, client_table_text, client_table_feature_text, divider_hr_color = \
            COLOR_HUMAN_BODY_TEXT, COLOR_HUMAN_H1_TITLE, COLOR_HUMAN_H3_SUBHEAD, COLOR_HUMAN_H4_SUBHEAD, \
            COLOR_HUMAN_HEADER_QUOTE, COLOR_HUMAN_CAPTION_TEXT, COLOR_HUMAN_TABLE_TEXT, COLOR_HUMAN_TABLE_HEADER, \
            COLOR_HUMAN_TABLE_GRID, COLOR_HUMAN_CLIENT_TABLE_HEADER_BG, COLOR_HUMAN_CLIENT_TABLE_GRID, \
            COLOR_HUMAN_CLIENT_TABLE_TEXT, COLOR_HUMAN_CLIENT_TABLE_FEATURE_TEXT, COLOR_HUMAN_DIVIDER

        # Use instance attributes for fonts, set by _register_fonts
        sans_font = getattr(self, 'sans_font', 'Helvetica')
        sans_bold_font = getattr(self, 'sans_bold_font', 'Helvetica-Bold')
        sans_italic_font = getattr(self, 'sans_italic_font', 'Helvetica-Oblique')
        serif_font = getattr(self, 'serif_font', 'Times-Roman')
        serif_bold_font = getattr(self, 'serif_bold_font', 'Times-Bold')
        serif_italic_font = 'DejaVuSerif-Italic' if 'DejaVuSerif-Italic' in getattr(self, 'REGISTERED_FONT_NAMES', []) else 'Times-Italic'

        styles.add(ParagraphStyle(name="BodyStyle", parent=styles['Normal'], fontName=sans_font, fontSize=11, leading=16, textColor=body_color, spaceAfter=6, alignment=4, allowWidows=1, allowOrphans=1))
        styles.add(ParagraphStyle(name="ListStyle", parent=styles['BodyStyle'], leftIndent=inch*0.35, bulletIndent=inch*0.1, bulletText='•', spaceBefore=3, spaceAfter=3, alignment=0))
        styles.add(ParagraphStyle(name="HeaderQuoteStyle", parent=styles['Normal'], fontName=sans_italic_font, fontSize=12, textColor=header_quote_color, alignment=1, leftIndent=inch*0.5, rightIndent=inch*0.5, spaceBefore=4, spaceAfter=10))
        styles.add(ParagraphStyle(name="InlineQuoteStyle", parent=styles['Italic'], fontName=sans_italic_font, fontSize=10, textColor=body_color, leftIndent=inch*0.4, rightIndent=inch*0.4, spaceBefore=10, spaceAfter=10, borderPadding=(8,8,8,8)))
        styles.add(ParagraphStyle(name="H1Style", parent=styles['h1'], fontName=serif_bold_font, fontSize=20, textColor=h1_color, alignment=1, spaceBefore=12, spaceAfter=6, keepWithNext=1))
        styles.add(ParagraphStyle(name="H3Style", parent=styles['h3'], fontName=sans_bold_font, fontSize=14, textColor=h3_color, spaceBefore=12, spaceAfter=4, keepWithNext=1, alignment=0))
        styles.add(ParagraphStyle(name="H4Style", parent=styles['h4'], fontName=sans_bold_font, fontSize=11, textColor=h4_color, spaceBefore=8, spaceAfter=2, keepWithNext=1, leftIndent=inch*0.1, alignment=0))
        styles.add(ParagraphStyle(name='CoverTitle', parent=styles['H1Style'], fontName=serif_bold_font, fontSize=32, alignment=1, spaceBefore=2.5*inch, textColor=h1_color))
        styles.add(ParagraphStyle(name='CoverSubTitle', parent=styles['BodyStyle'], fontName=sans_font, fontSize=20, alignment=1, spaceBefore=0, spaceAfter=0.5*inch, textColor=body_color))
        styles.add(ParagraphStyle(name="CaptionStyle", parent=styles['Normal'], fontName=sans_italic_font, fontSize=9, leading=11, textColor=caption_color, alignment=1, spaceBefore=2, spaceAfter=0))
        styles.add(ParagraphStyle(name="TableBodyStyle", parent=styles['BodyStyle'], fontSize=9, leading=11, spaceBefore=2, spaceAfter=2, textColor=table_text_color, alignment=1))
        styles.add(ParagraphStyle(name="TableHeaderStyle", parent=styles['BodyStyle'], fontName=sans_bold_font, fontSize=10, leading=12, textColor=table_header_color, alignment=1))
        styles.add(ParagraphStyle(name="JournalLineStyle", parent=styles['BodyStyle'], fontSize=11, leading=14, textColor=body_color, spaceAfter=6, alignment=0))
        styles.add(ParagraphStyle(name="ClientTableFeatureStyle", parent=styles['BodyStyle'], fontName=sans_bold_font, fontSize=10, leading=12, textColor=client_table_feature_text, alignment=0))
        styles.add(ParagraphStyle(name="ClientTableDataStyle", parent=styles['BodyStyle'], fontName=sans_font, fontSize=10, leading=12, textColor=client_table_text, alignment=0))
        styles.add(ParagraphStyle(name="AspectLocationStyle", parent=styles['BodyStyle'], fontName=sans_italic_font, fontSize=10, spaceBefore=0, spaceAfter=4, alignment=0))
        styles.add(ParagraphStyle(
            name="HighlightStyle", parent=styles['BodyStyle'], fontName=sans_italic_font, fontSize=12, leading=15,
            textColor=(COLOR_PET_HIGHLIGHT_TEXT if self.is_pet_report else COLOR_HUMAN_INLINE_QUOTE_TEXT), # Use appropriate text color
            backColor=(COLOR_PET_HIGHLIGHT_BG if self.is_pet_report else None), # Pet highlight, human no background or different
            alignment=1, leftIndent=inch*0.3, rightIndent=inch*0.3, spaceBefore=12, spaceAfter=12, borderPadding=(6,6,6,6),
        ))
        logger.info(f"  PDF styles created (V{pdf_generator_version_marker}).")
        return styles

    def _get_section_override(self, section_id, key):
        section_overrides = self.current_occasion_style.get('section_overrides', {})
        if section_id in section_overrides:
            return section_overrides[section_id].get(key)
        return None

    def _get_pet_section_divider_path(self, section_id_tag): # Changed arg name to match caller
        if not self.is_pet_report: return None
        
        # This method is specific to PetPDFBuilder and should be there.
        # If HumanPDFBuilderBase needs a generic way, it should call this on self
        # and PetPDFBuilder would override it.
        # For now, this method is defined in HumanPDFBuilderBase but only really makes sense if called by PetPDFBuilder's logic.
        # PetPDFBuilder should have its own _get_section_divider_path that uses STRIP_DIVIDERS.
        # This base version will use the single 'divider_image' from pet_default if no specific JSON path.
        
        # For Human reports, section dividers are not handled this way by default, only general divider.
        # This pet-specific logic in base might be confusing.
        # Let's assume this is more of a placeholder for how a subclass might handle it.
        # The true pet divider logic is in PetPDFBuilder.
        
        # Fallback to the general pet divider path determined in __init__
        if self.general_divider_path and os.path.exists(self.general_divider_path) and self.general_divider_path != DEFAULT_HUMAN_DIVIDER_IMAGE:
            logger.debug(f"Base (for pet): Using general pet divider for section tag '{section_id_tag}': {self.general_divider_path}")
            return self.general_divider_path
        # If general pet divider is not set or is same as human, or missing, this implies no special pet divider here.
        return None # No specific base logic for section-tagged pet dividers. PetPDFBuilder handles this.


    # <<< CORRECTED _add_image METHOD >>>
    def _add_image(self, image_path_or_reader, width=None, height=None, center=True, is_divider=False, is_cover=False, story_list=None, **kwargs): # Added story_list and **kwargs
        """Helper to add an image, handling potential errors, ImageReader, and fallback."""
        
        path_to_use = image_path_or_reader
        
        # If an ImageReader object is passed, try to get its filename
        if isinstance(image_path_or_reader, ImageReader):
            logger.debug(f"_add_image received ImageReader, attempting to extract filename.")
            extracted_path = getattr(image_path_or_reader, "_fileName", None)
            if not extracted_path and hasattr(image_path_or_reader, "fp") and isinstance(image_path_or_reader.fp, str):
                extracted_path = image_path_or_reader.fp
            if extracted_path:
                path_to_use = extracted_path
                logger.debug(f"Extracted path from ImageReader: {path_to_use}")
            else:
                logger.error(f"Could not extract usable path from ImageReader: {image_path_or_reader}. Cannot add image.")
                return False # Cannot proceed without a valid path

        # Now path_to_use should be a string path
        if not path_to_use or not isinstance(path_to_use, (str, os.PathLike)):
            logger.error(f"Invalid image path type for _add_image: {path_to_use} (type: {type(path_to_use)})")
            return False

        resolved_path_exists = os.path.exists(path_to_use)

        if not resolved_path_exists:
            logger.warning(f"Image not found at resolved path: '{path_to_use}'. Attempting fallback based on type.")
            original_image_path_for_log = path_to_use 
            
            # Determine appropriate default based on context
            current_default_cover = DEFAULT_PET_COVER_IMAGE if self.is_pet_report else DEFAULT_HUMAN_COVER_IMAGE
            current_default_divider = DEFAULT_PET_DIVIDER_IMAGE if self.is_pet_report else DEFAULT_HUMAN_DIVIDER_IMAGE

            if is_cover and os.path.exists(current_default_cover):
                path_to_use = current_default_cover
                logger.info(f"Using default {'pet' if self.is_pet_report else 'human'} cover fallback: {path_to_use} for original: {original_image_path_for_log}")
            elif is_divider and os.path.exists(current_default_divider):
                path_to_use = current_default_divider
                logger.info(f"Using default {'pet' if self.is_pet_report else 'human'} divider fallback: {path_to_use} for original: {original_image_path_for_log}")
            
            resolved_path_exists = os.path.exists(path_to_use) # Re-check after fallback

        if not resolved_path_exists:
            logger.error(f"Image (and fallback) not found or path is invalid: {image_path_or_reader}")
            target_story = story_list if story_list is not None else self.story
            if hasattr(self, 'styles') and 'BodyStyle' in self.styles:
                 target_story.append(Paragraph(f"[Image Missing: {os.path.basename(str(path_to_use) or 'No Path')}]", self.styles['BodyStyle']))
            return False

        try:
            # Create ReportLab Image object DIRECTLY FROM THE FILE PATH STRING
            rl_img = Image(path_to_use)

            img_w_orig, img_h_orig = rl_img.drawWidth, rl_img.drawHeight
            aspect = img_h_orig / float(img_w_orig) if img_w_orig != 0 else 1

            # Use provided width/height or calculate based on aspect ratio
            final_width, final_height = width, height

            if width and not height: final_height = width * aspect
            elif height and not width: final_width = height / aspect if aspect != 0 else width
            elif not width and not height: # Auto-scale to fit frame_width
                frame_width = self.doc.width if hasattr(self, 'doc') else LETTER[0] - 1.5*inch
                if img_w_orig > frame_width:
                    scale_factor = frame_width / img_w_orig
                    final_width, final_height = frame_width, img_h_orig * scale_factor
                    logger.debug(f"Scaled image '{os.path.basename(path_to_use)}' to fit frame width.")
                else: final_width, final_height = img_w_orig, img_h_orig # Use original if smaller
            
            rl_img.drawWidth = final_width
            rl_img.drawHeight = final_height
            
            if center or kwargs.get('center', False): # Check kwargs for 'center' if not passed directly
                rl_img.hAlign = 'CENTER'
            
            target_story = story_list if story_list is not None else self.story
            target_story.append(rl_img)
            logger.debug(f"Added image: {os.path.basename(path_to_use)} to story.")
            return True
        except Exception as e:
            logger.error(f"Could not add image '{path_to_use}': {e}", exc_info=True)
            target_story = story_list if story_list is not None else self.story
            if hasattr(self, 'styles') and 'BodyStyle' in self.styles:
                 target_story.append(Paragraph(f"[Error loading image: {os.path.basename(path_to_use)}]", self.styles['BodyStyle']))
            return False

    def _build_aspect_table(self, planet_name, aspect_data):
        try:
            table_body_style = self.styles['TableBodyStyle']
            table_header_style = self.styles['TableHeaderStyle']
            table_grid_color = COLOR_PET_TABLE_GRID if self.is_pet_report else COLOR_HUMAN_TABLE_GRID
        except KeyError as e: logger.error(f"Missing style for _build_aspect_table: {e}"); return None

        if not aspect_data: return None
        aspects_to_show = [a for a in aspect_data if isinstance(a, dict) and a.get('type') == 'major']
        if not aspects_to_show: logger.debug(f"No major aspects for {planet_name}."); return None

        try:
            data = [[Paragraph('Aspect', table_header_style), Paragraph('Planet 2', table_header_style), Paragraph('Orb', table_header_style)]]
            for asp_info in aspects_to_show:
                orb = asp_info.get('orb', '?'); orb_str = f"{float(orb):.1f}°" if isinstance(orb, (int,float)) else str(orb)
                data.append([asp_info.get('aspect', '?').capitalize(), asp_info.get('planet2', '?'), orb_str])
            
            table = Table(data, colWidths=[1.5*inch, 1.5*inch, 0.75*inch])
            table.setStyle(TableStyle([
                ('TEXTCOLOR', (0,0), (-1,0), table_header_style.textColor), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('FONTNAME', (0,0), (-1,0), table_header_style.fontName),
                ('FONTSIZE', (0,0), (-1,0), table_header_style.fontSize), ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('TEXTCOLOR', (0,1), (-1,-1), table_body_style.textColor), ('FONTNAME', (0,1), (-1,-1), table_body_style.fontName),
                ('FONTSIZE', (0,1), (-1,-1), table_body_style.fontSize), ('GRID', (0,0), (-1,-1), 0.5, table_grid_color),
                ('LEFTPADDING', (0,0), (-1,-1), 3), ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,1), (-1,-1), 3),
            ]))
            logger.debug(f"Built aspect table for {planet_name}.")
            return table
        except Exception as e: logger.error(f"Error building aspect table for {planet_name}: {e}", exc_info=True); return None

    def _build_client_details_table(self, table_data):
        if not isinstance(table_data, dict): logger.error("Client details table_data not dict."); return Paragraph("[Error: Client Details]", self.styles['BodyStyle'])
        logger.info("      Building Client Details table...")
        try:
            feature_style = self.styles['ClientTableFeatureStyle']; data_style = self.styles['ClientTableDataStyle']
            table_grid_color = COLOR_PET_CLIENT_TABLE_GRID if self.is_pet_report else COLOR_HUMAN_CLIENT_TABLE_GRID
            table_header_bg = COLOR_PET_CLIENT_TABLE_HEADER_BG if self.is_pet_report else COLOR_HUMAN_CLIENT_TABLE_HEADER_BG
        except KeyError as e: logger.error(f"Missing style for _build_client_details_table: {e}"); return None

        def create_paragraph(text, style): # Local helper
            if text is None: text = ""
            if not isinstance(text, str): text = str(text)
            safe_text = re.sub(r"<\s*(voice|prosody|say-as)[^>]*>.*?<\s*/\s*(voice|prosody|say-as)\s*>", "", text, flags=re.I|re.S).strip()
            safe_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_text)
            safe_text = re.sub(r'(?<![<\w])\*([^*]+)\*(?![>\w])', r'<i>\1</i>', safe_text)
            escaped_text = html.escape(safe_text).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>").replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
            escaped_text = re.sub(r'&lt;font name=[\'"]?([^\'"]+)[\'"]?&gt;', r'<font name="\1">', escaped_text).replace("&lt;/font&gt;", "</font>")
            try: return Paragraph(escaped_text, style)
            except: return Paragraph(f"[Render Error: {html.escape(safe_text[:30])}...]", self.styles.get('BodyStyle', getSampleStyleSheet()['Normal']))
        
        table_content = []
        for feature, item_data in table_data.items():
            details = item_data.get('details', '?') if isinstance(item_data, dict) else item_data
            symbol = item_data.get('symbol', '') if isinstance(item_data, dict) else ''
            text_val = f"{details} {symbol}".strip() if symbol else str(details)
            table_content.append([create_paragraph(f"<b>{feature}</b>", feature_style), create_paragraph(text_val, data_style)])
        
        if not table_content: logger.warning("No data for Client Details table."); return Paragraph("[Client Details Table empty]", self.styles['BodyStyle'])
        
        table = Table(table_content, colWidths=[1.8*inch, 4.0*inch], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, table_grid_color), ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('BACKGROUND', (0,0), (0,-1), table_header_bg), 
        ]))
        logger.info("      Client Details table created.")
        return KeepTogether([table])

    def build_pdf_story(self):
        logger.info(f"Building PDF story for '{self.client_name}', Occasion: '{self.occasion_mode}', Type: {'Pet' if self.is_pet_report else 'Human'}...")
        self.story = []
        
        # Set doc attributes from the builder instance for page_decorator
        self.doc.is_pet_report = self.is_pet_report
        self.doc.theme_bg_color = getattr(self, 'doc_theme_bg_color', COLOR_PET_BG if self.is_pet_report else COLOR_HUMAN_BG)
        self.doc.theme_border_color = getattr(self, 'doc_theme_border_color', COLOR_PET_PAGE_BORDER if self.is_pet_report else COLOR_HUMAN_PAGE_BORDER)
        self.doc.theme_background_image_path = getattr(self, 'doc_theme_background_image_path', None)


        frame_cover_or_art = Frame(0,0,self.doc.pagesize[0],self.doc.pagesize[1],id='cover_art_frame',leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0)
        main_frame_padding = 0.25*inch
        frame_main = Frame(self.doc.leftMargin,self.doc.bottomMargin,self.doc.width,self.doc.height,id='main_frame',leftPadding=main_frame_padding,bottomPadding=main_frame_padding,rightPadding=main_frame_padding,topPadding=main_frame_padding)
        template_cover = PageTemplate(id='CoverPage', frames=[frame_cover_or_art], pagesize=LETTER)
        template_main = PageTemplate(id='MainPage', frames=[frame_main], onPage=page_decorator, pagesize=LETTER)
        self.doc.addPageTemplates([template_cover, template_main])

        logger.info("  Adding Cover Page content...")
        self.story.append(NextPageTemplate('CoverPage'))
        
        # Determine which cover image path to use: one explicitly set by subclass (PetPDFBuilder) or the one from __init__ (Human default/occasion)
        cover_image_to_use = self._get_cover_image_path() # This will call PetPDFBuilder's override if it's a pet instance

        self._add_image(cover_image_to_use, width=self.doc.pagesize[0], height=self.doc.pagesize[1], is_cover=True, story_list=self.story) # Pass self.story

        cover_title_text = self._get_cover_title() # This allows subclasses to override title easily
        self.story.append(Paragraph(cover_title_text, self.styles['CoverTitle']))
        self.story.append(Paragraph(f"Prepared for {self.client_name}", self.styles['CoverSubTitle']))
        self.story.append(NextPageTemplate('MainPage')); self.story.append(PageBreak())

        if isinstance(self.PROMPTS_TO_USE, list): sorted_prompt_structures = self.PROMPTS_TO_USE
        else: 
            logger.warning("PROMPTS_TO_USE not list, sorting dict keys."); 
            sorted_keys = sorted(self.PROMPTS_TO_USE.keys(), key=lambda x: int(x.split('_')[0]) if x.split('_')[0].isdigit() else 99)
            sorted_prompt_structures = [self.PROMPTS_TO_USE[key] for key in sorted_keys]

        aspects_dict = self.chart_data.get('aspects', {}) if isinstance(self.chart_data, dict) else {}
        PARA_SPACER_HEIGHT = 6

        for i, prompt_struct in enumerate(sorted_prompt_structures):
            section_key = prompt_struct.get("section_id");
            if not section_key or section_key == "cover": continue
            logger.info(f"Processing section: {section_key}");
            section_content_data = self.sections.get(section_key, {})
            
            header_override = self._get_section_override(section_key, "header")
            section_header = header_override if header_override is not None else prompt_struct.get('header', f'Section {section_key}')
            quote_override = self._get_section_override(section_key, "quote")
            section_quote_default = prompt_struct.get('quote', '')
            
            if quote_override is not None: section_quote_to_render = quote_override
            elif self.is_pet_report: section_quote_to_render = None # Trigger random pet quote
            else: section_quote_to_render = section_quote_default
            
            intro_override = self._get_section_override(section_key, "static_intro")
            section_static_intro = intro_override if intro_override is not None else (STATIC_INTROS_PET.get(section_key, '') if self.is_pet_report else prompt_struct.get('static_intro', ''))
            
            static_texts = [section_header, section_quote_to_render, section_static_intro]
            fmt_texts = []
            for txt in static_texts:
                if isinstance(txt, str):
                    try: fmt_texts.append(txt.format(client_name=self.client_name, pet_name=self.client_name)) # Add pet_name for flexibility
                    except KeyError: fmt_texts.append(txt.format(client_name=self.client_name)) # Fallback
                    except Exception as e: logger.warning(f"Err fmt static text for {section_key}: {e}"); fmt_texts.append(txt)
                else: fmt_texts.append(txt)
            
            section_header_fmt, section_quote_render, section_static_intro_fmt = fmt_texts[0], fmt_texts[1], fmt_texts[2]

            if section_header_fmt:
                try: self.story.append(Paragraph(f"<b>{clean_font_tags(section_header_fmt)}</b>", self.styles["H1Style"]))
                except Exception as e: logger.error(f"Err H1 Para for {section_key}: {e}"); self.story.append(Paragraph("[HeaderErr]",self.styles["H1Style"]))
                self.story.append(Spacer(1, 0.1*inch))

            if self.is_pet_report and section_quote_render is None:
                if self.pet_quotes:
                    try: self.story.append(Paragraph(f"“{clean_font_tags(random.choice(self.pet_quotes))}”", self.styles['HighlightStyle'])); self.story.append(Spacer(1,0.1*inch))
                    except Exception as e: logger.error(f"Err pet quote for {section_key}: {e}"); self.story.append(Paragraph("[PetQuoteErr]",self.styles['BodyStyle']))
                else: logger.debug(f"No pet quotes for {section_key}.")
            elif section_quote_render:
                quote_style_to_use = self.styles['HighlightStyle'] if self.is_pet_report else self.styles["HeaderQuoteStyle"]
                try: self.story.append(Paragraph(f"<i>{clean_font_tags(section_quote_render)}</i>", quote_style_to_use)); self.story.append(Spacer(1,0.1*inch))
                except Exception as e: logger.error(f"Err Quote Para for {section_key}: {e}"); self.story.append(Paragraph("[QuoteErr]",self.styles["HeaderQuoteStyle"]))

            if section_static_intro_fmt:
                for line in section_static_intro_fmt.split('\n'):
                    if line.strip(): 
                        try: self.story.append(Paragraph(clean_font_tags(line.strip()), self.styles['BodyStyle']))
                        except Exception as e: logger.error(f"Err Intro Para for {section_key}: {e}"); self.story.append(Paragraph("[IntroErr]",self.styles['BodyStyle']))
                self.story.append(Spacer(1, 0.1*inch))

            try: # Section Body
                if section_key == "02_Client_Details": # This key should be consistent
                    table_data = section_content_data.get('table_data')
                    if table_data: client_table = self._build_client_details_table(table_data); 
                    if client_table: self.story.append(client_table)
                    else: logger.warning(f"Client details table failed/no data for {section_key}")
                elif section_key == "03_Chart_Wheel":
                    if self.chart_image_path and os.path.exists(self.chart_image_path):
                        logger.info("      Adding Chart Image..."); 
                        self._add_image(self.chart_image_path, width=self.doc.width*0.8, center=True, story_list=self.story)
                        self.story.append(Spacer(1,0.1*inch))
                    else: logger.warning("Chart image missing."); self.story.append(Paragraph("[Chart Missing]",self.styles['BodyStyle'])).append(Spacer(1,0.1*inch))
                else:
                    ai_content = section_content_data.get('ai_generated_content', '')
                    if ai_content and not any(err_placeholder in ai_content for err_placeholder in ["[AI Skipped]", "[SYSTEM ERROR", "[ERROR:"]):
                        cleaned_body = clean_ai_content_for_pdf(ai_content) # Centralized cleaning
                        body_lines = cleaned_body.splitlines(); current_para = ""; current_planet = None
                        for i_line, line in enumerate(body_lines):
                            try:
                                proc_line = apply_basic_markdown_to_reportlab(line); stripped = proc_line.strip()
                                if not stripped and not current_para.strip(): continue
                                h3_match = re.match(r"^\s*<b>(.*?)</b>", stripped); list_match = re.match(r"^\s*-\s+(.*)", proc_line)
                                div_match = stripped == '---'; journal_match = re.search(r"Journal Prompt:", proc_line, re.I)
                                special_line = False; style_to_use = None; content_to_parse = None

                                if h3_match: style_to_use=self.styles['H3Style']; content_to_parse=h3_match.group(1).strip(); special_line=True
                                elif journal_match: style_to_use=self.styles['H4Style']; content_to_parse=proc_line.strip(); special_line=True
                                elif list_match: style_to_use=self.styles['ListStyle']; content_to_parse=list_match.group(1).strip(); special_line=True
                                elif div_match: special_line=True # Handle divider
                                elif stripped_line: current_para += proc_line + "\n"
                                else: special_line=True # Empty line = para break

                                if special_line or (i_line == len(body_lines)-1 and current_para.strip()):
                                    if current_para.strip():
                                        try: self.story.append(Paragraph(current_para.strip(), self.styles['BodyStyle'])); self.story.append(Spacer(1,PARA_SPACER_HEIGHT/3))
                                        except: self.story.append(Paragraph("[BodyErr]",self.styles['BodyStyle']))
                                        current_para = ""
                                    if style_to_use and content_to_parse is not None:
                                        try: self.story.append(Paragraph(content_to_parse, style_to_use))
                                        except: self.story.append(Paragraph("[SpecialLineErr]",self.styles['BodyStyle']))
                                        # Aspect table logic / Journal lines after H3/H4
                                        if style_to_use==self.styles['H3Style'] and section_key=="09_Planetary_Analysis": # Example condition
                                            planet_name_from_header = extract_planet_from_header(content_to_parse) # You need this helper
                                            if planet_name_from_header and isinstance(aspects_dict, dict):
                                                planet_aspects = aspects_dict.get(planet_name_from_header,[])
                                                if planet_aspects: aspect_table = self._build_aspect_table(planet_name_from_header,planet_aspects)
                                                if aspect_table: self.story.append(Spacer(1,0.05*inch)); self.story.append(aspect_table); self.story.append(Spacer(1,0.1*inch))
                                        elif style_to_use==self.styles['H4Style'] and journal_match:
                                            self.story.append(Spacer(1,0.05*inch)); self.story.append(Paragraph("___" *15, self.styles['JournalLineStyle'])) # Using JournalLineStyle
                                            self.story.append(Paragraph("___" *15, self.styles['JournalLineStyle'])); self.story.append(Spacer(1,0.1*inch))
                                        elif style_to_use in [self.styles['H3Style'], self.styles['H4Style']] and (i_line==len(body_lines)-1 or not body_lines[i_line+1].strip()):
                                            self.story.append(Spacer(1,PARA_SPACER_HEIGHT-2))
                                    if div_match: self.story.append(HRFlowable(width="80%",thickness=1,color=divider_hr_color,spaceBefore=10,spaceAfter=10,hAlign='CENTER'))
                            except Exception as line_err: logger.error(f"Err proc line in {section_key}: {line_err}. Line: '{line[:50]}'"); self.story.append(Paragraph("[LineErr]",self.styles['BodyStyle'])); current_para=""
                        if current_para.strip(): # Remaining text
                            try: self.story.append(Paragraph(current_para.strip(), self.styles['BodyStyle']))
                            except: self.story.append(Paragraph("[FinalBodyErr]",self.styles['BodyStyle']))
                    else: logger.debug(f"No AI content for {section_key}.")
            except Exception as section_err: 
                logger.critical(f"Crit err proc section body {section_key}: {section_err}",exc_info=True)
                self.story.append(Paragraph(f"<b>[ERR PROC SECTION: {section_key}]</b>",self.styles['H3Style']))
                self.story.append(Paragraph(f"Details: {html.escape(str(section_err))}",self.styles['BodyStyle'])); self.story.append(PageBreak())

            # Add Divider Image
            # This logic needs to align with PetPDFBuilder's override for section-specific dividers
            if i < len(sorted_prompt_structures) - 1: # Not after last section
                divider_tag_from_prompt = prompt_struct.get("divider_tag", "default")
                # The call below will resolve to PetPDFBuilder._get_section_divider_path if self is a PetPDFBuilder instance
                # Or it will call this class's _get_pet_section_divider_path if called on HumanPDFBuilderBase instance and is_pet_report
                # Or use self.general_divider_path for human reports.
                
                divider_path_to_use = None
                if hasattr(self, '_get_section_divider_path') and callable(getattr(self, '_get_section_divider_path')):
                     # This will call PetPDFBuilder's override if it exists and self is a PetPDFBuilder instance
                    divider_path_to_use = self._get_section_divider_path(divider_tag_from_prompt) 
                
                if not divider_path_to_use: # Fallback if subclass method didn't return a path or if not a pet instance with specific logic
                    divider_path_to_use = self.general_divider_path # Fallback to the general divider for the current report type
                
                self.story.append(Spacer(1, 0.3 * inch))
                divider_width_to_use = self.doc.width * 0.8 if self.is_pet_report else 2 * inch
                self._add_image(divider_path_to_use, width=divider_width_to_use, center=True, is_divider=True, story_list=self.story) # Pass self.story
                self.story.append(Spacer(1, 0.3 * inch))
            else: self.story.append(Spacer(1, 0.5 * inch))
        
        try:
            logger.info("Building final PDF document from story...")
            self.doc.build(self.story)
            logger.info(f"PDF build complete: {self.output_path}")
            return True
        except Exception as e:
            logger.critical(f"[FATAL] PDF generation failed: {e}", exc_info=True)
            return False

def generate_astrology_pdf(
        output_path, sections, client_name, chart_data, chart_image_path,
        PROMPTS_TO_USE, SECTION_LAYOUT_PRESETS, occasion_mode="default",
        is_pet_report=False, pet_breed=None, **kwargs # Added **kwargs for species from pet module
    ):
    logger.info(f"Initiating PDF generation V{pdf_generator_version_marker}")
    logger.info(f"  Client: '{client_name}', Occasion: '{occasion_mode}', Type: {'Pet' if is_pet_report else 'Human'}")
    if is_pet_report: logger.info(f"  Pet Breed: {pet_breed if pet_breed else 'N/A'}, Species: {kwargs.get('species', 'N/A')}")
    logger.info(f"  Output Path: {output_path}")

    generation_context = {
        'sections': sections, 'client_name': client_name, 'chart_data': chart_data,
        'chart_image_path': chart_image_path, 'PROMPTS_TO_USE': PROMPTS_TO_USE,
        'SECTION_LAYOUT_PRESETS': SECTION_LAYOUT_PRESETS, 'occasion_mode': occasion_mode,
        'is_pet_report': is_pet_report, 'pet_breed': pet_breed,
        'species': kwargs.get('species') # Pass species through if provided
    }
    try:
        # If it's a pet report, instantiate PetPDFBuilder, otherwise DejaVuPDFBuilder (Human)
        # This requires PetPDFBuilder to be defined/imported if is_pet_report is True
        if is_pet_report:
            try:
                from pdf_generator_pet import PetPDFBuilder # Moved import here
                builder = PetPDFBuilder(output_path, generation_context)
                logger.info("Using PetPDFBuilder for pet report.")
            except ImportError:
                logger.error("PetPDFBuilder could not be imported from pdf_generator_pet. Falling back to DejaVuPDFBuilder for pet report (styling may be incorrect).")
                builder = DejaVuPDFBuilder(output_path, generation_context) # Fallback
        else:
            builder = DejaVuPDFBuilder(output_path, generation_context)
            logger.info("Using DejaVuPDFBuilder for human report.")
            
        success = builder.build_pdf_story()
        return success
    except Exception as e:
        logger.critical(f"[FATAL] PDF generation failed: {e}", exc_info=True)
        return False

def clean_font_tags(text):
    if not isinstance(text, str): return str(text) if text is not None else ""
    cleaned = re.sub(r'<font[^>]*>', '', text, flags=re.I)
    return cleaned.replace('</font>', '')

def clean_ai_content_for_pdf(text): # More comprehensive cleaning
    if not isinstance(text, str): return ""
    text = re.sub(r"<\s*(voice|prosody|say-as)[^>]*>.*?<\s*/\s*(voice|prosody|say-as)\s*>", "", text, flags=re.I|re.S).strip()
    text = re.sub(r"Content to Generate \(within SSML tags below\):[\s\n]*", "", text).strip()
    text = re.sub(r"^You are .*?\n.*?\n.*?\n(?:.*\n)?\n", "", text, flags=re.S).strip() # More robust persona removal
    text = re.sub(r"Writing Style / Techniques:.*?(\n\n|\Z)", "", text, flags=re.S).strip() # Stop at double newline or end
    text = re.sub(r"Oracle Directive:.*?(\n\n|\Z)", "", text, flags=re.S).strip()
    return text

def extract_planet_from_header(header_text): # Dummy helper, needs robust implementation
    if not isinstance(header_text, str): return None
    # Simplified: Assumes planet is the first word if not a symbol
    # This should ideally use the SYMBOLS dict for accuracy
    # Check for SYMBOLS existence for robustness
    if 'SYMBOLS' in globals() and isinstance(SYMBOLS, dict):
        for planet, symbol in SYMBOLS.items():
            if header_text.startswith(symbol) or header_text.lower().startswith(planet.lower()):
                return planet
    # Fallback for simple word match if symbol not found first
    first_word = header_text.split(" ")[0].replace("<b>","").replace("</b>","").strip()
    if first_word in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron"]: # Common list
        return first_word
    return None


# --- Assume SYMBOLS dictionary is available ---
# For standalone test, provide a dummy. In project, it's imported.
if 'SYMBOLS' not in globals(): # Check if SYMBOLS isn't already defined/imported
    logger.warning("SYMBOLS not found globally. Using dummy SYMBOLS for testing pdf_generator_human.")
    SYMBOLS = { "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂", "Jupiter": "♃", "Saturn": "♄", "Uranus": "⛢", "Neptune": "♆", "Pluto": "♇" }


if __name__ == '__main__':
    if not logger.handlers:
        test_logger_handler = logging.StreamHandler(); test_logger_formatter = logging.Formatter('%(asctime)s - %(levelname)s - TEST_HUMAN:%(lineno)d - %(message)s')
        test_logger_handler.setFormatter(test_logger_formatter); logger.addHandler(test_logger_handler); logger.setLevel(logging.DEBUG)
    logger.info("Running pdf_generator_human.py (DejaVuPDFBuilder) directly for testing...")

    mock_sections_human = {
        "cover": {},
        "01_Mythic_Prologue": {"ai_generated_content": "Prologue: <b>Bold</b> and <i>italic</i>.\n\nNew Para."},
        "02_Client_Details": {"table_data": {"Name": {"details": "Test Human"}, "Sun": {"details": "Leo", "symbol": "☉"}}},
        "03_Chart_Wheel": {},
        "05_Core_Essence": {"ai_generated_content": "Core essence text. --- A divider. Journal Prompt: Reflect."},
        "09_Planetary_Analysis": {"ai_generated_content": "<b>Sun in Aries</b>\nSun analysis.\n\n<b>Moon in Taurus</b>\nMoon analysis."},
    }
    mock_prompts_list_human = [
        {"section_id": "cover", "header": "Your Cosmic Blueprint"},
        {"section_id": "01_Mythic_Prologue", "header": "Mythic Prologue", "quote": "A journey begins.", "static_intro": "Welcome."},
        {"section_id": "02_Client_Details", "header": "Your Natal Details"},
        {"section_id": "03_Chart_Wheel", "header": "Your Birth Chart"},
        {"section_id": "05_Core_Essence", "header": "Core Essence Revealed"},
        {"section_id": "09_Planetary_Analysis", "header": "Planetary Insights"},
    ]
    mock_chart_data_human = { "aspects": { "Sun": [{"planet1":"Sun", "planet2":"Moon", "aspect":"Trine", "orb":1.0, "type":"major"}] }, "birth_details": {"chart_ruler":"Sun"}}
    
    test_output_dir = os.path.join(SCRIPT_DIR, "test_pdf_output_human") # Output in human script's dir
    os.makedirs(test_output_dir, exist_ok=True)

    # Test Human Report
    logger.info(f"\n--- TESTING HUMAN REPORT (using DejaVuPDFBuilder directly) ---")
    test_output_path_human = os.path.join(test_output_dir, f"test_direct_human_report_{pdf_generator_version_marker}.pdf")
    
    # Make sure dummy occasion_styles.json and pet_quotes.json exist for base class init
    if not os.path.exists(os.path.join(DATA_JSONS_DIR, 'occasion_styles.json')):
        with open(os.path.join(DATA_JSONS_DIR, 'occasion_styles.json'), 'w') as f_json: json.dump({"human_default": {"cover_image": "images/covers/default_cover.jpg"}}, f_json)
        logger.info("Created dummy occasion_styles.json for human test.")

    if not os.path.exists(os.path.join(DATA_JSONS_DIR, 'pet_quotes.json')):
         with open(os.path.join(DATA_JSONS_DIR, 'pet_quotes.json'), 'w') as f_json: json.dump(["Test pet quote"], f_json)
         logger.info("Created dummy pet_quotes.json for human test.")


    success_human = generate_astrology_pdf(
        output_path=test_output_path_human, sections=mock_sections_human, client_name="Test Human",
        chart_data=mock_chart_data_human, chart_image_path=None, PROMPTS_TO_USE=mock_prompts_list_human,
        SECTION_LAYOUT_PRESETS={}, occasion_mode="human_default", is_pet_report=False
    )
    if success_human: logger.info(f"Successfully generated test HUMAN PDF: {test_output_path_human}")
    else: logger.error(f"Failed to generate test HUMAN PDF.")
    logger.info("--- DejaVuPDFBuilder (Human) Test Complete ---")