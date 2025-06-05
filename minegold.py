import os
import io
import re
import logging
import string
from unidecode import unidecode
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

def handle_hyphenation(text):
    """Fix words broken by hyphenation across lines"""
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    text = re.sub(r'\s+-\s+', ' ', text)
    return text

def clean_whitespace(text):
    """Normalize all whitespace characters"""
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def remove_control_characters(text):
    """Remove non-printable control characters"""
    return ''.join(ch for ch in text if ch not in string.control)

def clean_special_chars(text):
    """Handle special characters and symbols"""
    text = re.sub(r'[_\-\|/+~*=]{2,}', ' ', text)
    return re.sub(r'[^\w\s@.,!?&%$#()\-]', '', text)

def remove_header_footer(text):
    """Remove common header/footer patterns"""
    patterns = [
        r'\bpage\s*\d+\b',
        r'\bconfidential\b',
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        r'^[\s\S]{0,50}resume[\s\S]{0,50}$',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text

def clean_text_pipeline(text):
    """Text cleaning pipeline"""
    cleaning_steps = [
        remove_control_characters,
        handle_hyphenation,
        lambda x: unidecode(x),
        clean_whitespace,
        remove_header_footer,
        clean_special_chars,
        lambda x: re.sub(r'\b(?:email|phone|http[s]?://)\S+\b', '', x),
        lambda x: re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', x),
        lambda x: re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', x),
        lambda x: re.sub(r'\u2022|\u25CF|\u25E6|\u2043', ' ', x),
        lambda x: re.sub(r'\d{10,}', '', x),
    ]
    
    for step in cleaning_steps:
        try:
            text = step(text)
        except Exception as e:
            logger.warning(f"Cleaning step failed: {str(e)}")
            continue
            
    return text

def process_pdf(pdf_path):
    """Main PDF processing function with fixed PDFMiner implementation"""
    try:
        logger.info(f"Processing PDF: {pdf_path}")
        
        rsrcmgr = PDFResourceManager()
        output_stream = io.StringIO()
        laparams = LAParams()
        device = TextConverter(rsrcmgr, output_stream, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        full_text = []

        with open(pdf_path, 'rb') as fp:
            for page in PDFPage.get_pages(fp):
                interpreter.process_page(page)
                page_text = output_stream.getvalue()
                if page_text.strip():
                    full_text.append(clean_text_pipeline(page_text))
                output_stream.truncate(0)
                output_stream.seek(0)
        
        device.close()
        output_stream.close()
        
        if not full_text:
            raise ValueError("No text could be extracted from PDF")
            
        final_text = ' '.join(full_text)
        return clean_text_pipeline(final_text)

    except Exception as e:
        logger.error(f"PDF Processing Error: {str(e)}", exc_info=True)
        raise