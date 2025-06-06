# pdf_generator.py

try:
    # Use the pet-specific PDF generator
    from pdf_generator_pet import generate_astrology_pdf, pdf_generator_version_marker
except ImportError:
    # Fallback to the human PDF generator (once it’s finalised)
    from pdf_generator_human import generate_astrology_pdf, pdf_generator_version_marker
