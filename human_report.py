# human_report.py
# Standalone PDF generator for Human Astrology Reports

import os
import json
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white # Basic colors
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak, Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import html
import re # For basic markdown

# --- Global Fallback Font Names ---
FALLBACK_SANS_FONT = 'Helvetica'
FALLBACK_SANS_BOLD_FONT = 'Helvetica-Bold'
FALLBACK_SANS_ITALIC_FONT = 'Helvetica-Oblique'
FALLBACK_SERIF_FONT = 'Times-Roman'
FALLBACK_SERIF_BOLD_FONT = 'Times-Bold'

def register_fonts(fonts_base_dir):
    """Registers DejaVu fonts if available, otherwise logs warnings."""
    registered_sans = False
    registered_serif = False # In case you want to use DejaVuSerif later

    fonts_to_try = {
        'DejaVuSans': os.path.join(fonts_base_dir, 'DejaVuSans.ttf'),
        'DejaVuSans-Bold': os.path.join(fonts_base_dir, 'DejaVuSans-Bold.ttf'),
        'DejaVuSans-Oblique': os.path.join(fonts_base_dir, 'DejaVuSans-Oblique.ttf'),
        'DejaVuSans-BoldOblique': os.path.join(fonts_base_dir, 'DejaVuSans-BoldOblique.ttf'),
        # Example for Serif if you add it later
        # 'DejaVuSerif': os.path.join(fonts_base_dir, 'DejaVuSerif.ttf'),
        # 'DejaVuSerif-Bold': os.path.join(fonts_base_dir, 'DejaVuSerif-Bold.ttf'),
    }
    font_mapping = {
        'sans': FALLBACK_SANS_FONT, 'sans_bold': FALLBACK_SANS_BOLD_FONT, 'sans_italic': FALLBACK_SANS_ITALIC_FONT,
        'serif': FALLBACK_SERIF_FONT, 'serif_bold': FALLBACK_SERIF_BOLD_FONT
    }

    for name, path in fonts_to_try.items():
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                print(f"INFO: Registered font: {name} from {path}")
                if name == 'DejaVuSans': font_mapping['sans'] = 'DejaVuSans'; registered_sans = True
                if name == 'DejaVuSans-Bold': font_mapping['sans_bold'] = 'DejaVuSans-Bold'
                if name == 'DejaVuSans-Oblique': font_mapping['sans_italic'] = 'DejaVuSans-Oblique'
                # Add similar for DejaVuSerif if you implement it
            except Exception as e:
                print(f"WARNING: Could not register font {name} from {path}: {e}")
        else:
            print(f"WARNING: Font file not found: {path} for {name}")

    if not registered_sans:
        print(f"WARNING: DejaVuSans not found/registered. Falling back to {FALLBACK_SANS_FONT}.")
    
    return font_mapping

def apply_markdown_to_reportlab(text_line):
    if not isinstance(text_line, str): return str(text_line) if text_line is not None else ""
    line = html.escape(text_line) # Escape HTML special chars first
    line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
    line = re.sub(r'(?<![<\w])\*([^*_]+)\*(?![>\w])', r'<i>\1</i>', line) 
    line = re.sub(r'(?<![<\w])_([^*_]+)_(?![>\w])', r'<i>\1</i>', line)
    line = line.replace('\n', '<br/>') # Convert newlines to <br/>
    return line

def generate_human_pdf(output_path, client_name, sections_data, occasion_style_key, 
                       assets_base_dir, fonts_base_dir, data_jsons_dir):
    """
    Generates a standalone human astrology PDF.
    sections_data: List of dicts, e.g., [{'header': 'Title', 'ai_content': 'Body text...', 'quote': 'Optional'}]
    """
    print(f"HUMAN_REPORT: Generating PDF for {client_name} at {output_path}")
    print(f"HUMAN_REPORT: Using style key '{occasion_style_key}'")

    doc = SimpleDocTemplate(output_path, pagesize=LETTER,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    story = []

    # 1. Font Registration
    font_map = register_fonts(fonts_base_dir)

    # 2. Load Occasion Style
    occasion_styles_path = os.path.join(data_jsons_dir, 'occasion_styles.json')
    style_config = {}
    try:
        with open(occasion_styles_path, 'r', encoding='utf-8') as f:
            all_styles = json.load(f)
            style_config = all_styles.get(occasion_style_key, {})
        if not style_config:
            print(f"WARNING: Style key '{occasion_style_key}' not found in {occasion_styles_path}. Using defaults.")
    except Exception as e:
        print(f"ERROR: Could not load or parse {occasion_styles_path}: {e}. Using defaults.")

    cover_image_rel_path = style_config.get('cover_image', 'images/covers/human_default_cover.jpg') # Default fallback
    divider_image_rel_path = style_config.get('divider_image', 'images/dividers/human_default_divider.png') # Default fallback
    theme_color_hex = style_config.get('theme_color', '#4A4E69') # Default human_default color
    # font_choice = style_config.get('font', 'Serif') # 'Serif' or 'Sans'

    cover_image_abs_path = os.path.join(assets_base_dir, cover_image_rel_path)
    divider_image_abs_path = os.path.join(assets_base_dir, divider_image_rel_path)
    
    try:
        theme_color = HexColor(theme_color_hex)
    except:
        print(f"WARNING: Invalid theme_color HEX '{theme_color_hex}'. Defaulting to black.")
        theme_color = black

    # 3. Define Styles
    styles = StyleSheet1()
    styles.add(ParagraphStyle(name='CoverTitle', fontName=font_map['serif_bold'], fontSize=30, textColor=theme_color, alignment=1, spaceBefore=2*inch))
    styles.add(ParagraphStyle(name='CoverSubTitle', fontName=font_map['sans'], fontSize=18, textColor=black, alignment=1, spaceBefore=0.2*inch))
    styles.add(ParagraphStyle(name='H1', fontName=font_map['serif_bold'], fontSize=20, textColor=theme_color, spaceBefore=12, spaceAfter=6, alignment=0))
    styles.add(ParagraphStyle(name='Quote', fontName=font_map['sans_italic'], fontSize=11, textColor=colors.dimgray, alignment=1, spaceBefore=6, spaceAfter=12, leftIndent=0.5*inch, rightIndent=0.5*inch))
    styles.add(ParagraphStyle(name='Body', fontName=font_map['sans'], fontSize=10, textColor=black, leading=14, spaceAfter=6, alignment=4)) # Justified

    # 4. Build Story
    # Cover Page
    if os.path.exists(cover_image_abs_path):
        try: story.append(Image(cover_image_abs_path, width=doc.pagesize[0], height=doc.pagesize[1], kind='proportional')) # Full page proportional
        except Exception as e: print(f"ERROR adding cover image {cover_image_abs_path}: {e}")
    else: print(f"WARNING: Cover image not found: {cover_image_abs_path}")
    
    story.append(Paragraph(style_config.get('report_title', "Your Cosmic Blueprint"), styles['CoverTitle'])) # Get title from JSON or default
    story.append(Paragraph(f"Prepared for {client_name}", styles['CoverSubTitle']))
    story.append(PageBreak())

    # Content Pages
    for i, section in enumerate(sections_data): # sections_data is a list of dicts
        header_text = section.get('header', f"Section {i+1}")
        ai_content = section.get('ai_content', "No content for this section.")
        quote_text = section.get('quote') # From prompt_definitions via orchestrator

        if header_text:
            story.append(Paragraph(apply_markdown_to_reportlab(header_text), styles['H1']))
        
        if quote_text: # Add quote if available for the section
            story.append(Paragraph(apply_markdown_to_reportlab(f"<i>“{quote_text}”</i>"), styles['Quote']))

        # Add a general divider before the main body, unless it's the first content section after cover.
        # Or always add it if that's the style. For simplicity, adding after header/quote.
        if i > 0 or quote_text : # Add space or divider
             story.append(Spacer(1, 0.1*inch)) # Add a bit of space if there was a quote

        if os.path.exists(divider_image_abs_path):
            try: story.append(Image(divider_image_abs_path, width=doc.width - 1*inch, height=0.25*inch, kind='proportional', hAlign='CENTER')) # Centered, width adjusted
            except Exception as e: print(f"ERROR adding divider image {divider_image_abs_path}: {e}")
            story.append(Spacer(1, 0.2*inch))
        else: print(f"WARNING: Divider image not found: {divider_image_abs_path}")
        
        if ai_content:
            # Simple split by double newline for paragraphs
            for para_text in ai_content.split('\n\n'):
                if para_text.strip():
                    story.append(Paragraph(apply_markdown_to_reportlab(para_text.strip()), styles['Body']))
        
        if i < len(sections_data) - 1: # Don't add page break after the very last section
            story.append(PageBreak())

    try:
        doc.build(story)
        print(f"HUMAN_REPORT: Successfully generated {output_path}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to build human PDF {output_path}: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Simple test for human_report.py
    print("Running test for human_report.py...")
    
    # Define paths relative to this script for testing
    current_script_dir = os.path.dirname(os.path.realpath(__file__))
    mock_assets_dir = os.path.join(current_script_dir, 'assets') # Assumes 'assets' is sibling to script
    mock_fonts_dir = os.path.join(current_script_dir, 'fonts')   # Assumes 'fonts' is sibling
    mock_data_jsons_dir = os.path.join(current_script_dir, 'Data jsons')

    os.makedirs(mock_assets_dir, exist_ok=True)
    os.makedirs(os.path.join(mock_assets_dir, 'images', 'covers'), exist_ok=True)
    os.makedirs(os.path.join(mock_assets_dir, 'images', 'dividers'), exist_ok=True)
    os.makedirs(mock_fonts_dir, exist_ok=True)
    os.makedirs(mock_data_jsons_dir, exist_ok=True)
    
    # Create dummy occasion_styles.json for test
    dummy_styles_path = os.path.join(mock_data_jsons_dir, 'occasion_styles.json')
    if not os.path.exists(dummy_styles_path):
        with open(dummy_styles_path, 'w') as f_styles:
            json.dump({
                "human_default": {
                    "report_title": "My Human Cosmic Blueprint",
                    "cover_image": "images/covers/human_default_cover.jpg",
                    "divider_image": "images/dividers/human_default_divider.png",
                    "theme_color": "#336699",
                    "font": "Serif"
                }
            }, f_styles)
        print(f"Created dummy {dummy_styles_path}")

    # Create dummy assets for testing if they don't exist
    # (In a real scenario, these should exist)
    def create_dummy_png(path, text="Placeholder"):
        if not os.path.exists(path):
            try:
                from PIL import Image as PILImage, ImageDraw, ImageFont
                img = PILImage.new('RGB', (600, 800), color = 'lightgray')
                draw = ImageDraw.Draw(img)
                try: font = ImageFont.truetype("arial.ttf", 40)
                except IOError: font = ImageFont.load_default()
                draw.text((50, 350), text, font=font, fill=(0,0,0))
                img.save(path)
                print(f"Created dummy image: {path}")
            except ImportError: print(f"Pillow not installed, cannot create dummy image {path}. Please create it manually.")
            except Exception as e_pil: print(f"Error creating dummy {path}: {e_pil}")

    create_dummy_png(os.path.join(mock_assets_dir, "images/covers/human_default_cover.jpg"), "Human Cover")
    create_dummy_png(os.path.join(mock_assets_dir, "images/dividers/human_default_divider.png"), "Divider")
    # Create dummy DejaVuSans.ttf for testing font registration
    if not os.path.exists(os.path.join(mock_fonts_dir, "DejaVuSans.ttf")):
         print(f"WARNING: Please place DejaVuSans.ttf in {mock_fonts_dir} for a better test.")


    mock_sections = [
        {'header': 'Introduction Chapter', 'ai_content': 'This is the **introduction** to your amazing human report. It contains many *insights*.\n\nAnd a second paragraph here.', 'quote': 'To be or not to be.'},
        {'header': 'Your Core Essence', 'ai_content': 'You are _truly_ special. This section delves deep.\n\n - A bullet point\n - Another bullet point'},
    ]
    
    output_dir = os.path.join(current_script_dir, "test_output_standalone")
    os.makedirs(output_dir, exist_ok=True)
    test_pdf_path = os.path.join(output_dir, "standalone_human_report.pdf")

    generate_human_pdf(
        output_path=test_pdf_path,
        client_name="Test Human",
        sections_data=mock_sections,
        occasion_style_key="human_default",
        assets_base_dir=mock_assets_dir, # Pass the correct base for assets
        fonts_base_dir=mock_fonts_dir,
        data_jsons_dir=mock_data_jsons_dir
    )