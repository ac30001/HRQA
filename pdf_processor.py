import requests
import fitz  # PyMuPDF
import logging
import re
from urllib.parse import urlparse
from typing import List, Dict, Optional

class PDFProcessor:
    """Handles PDF downloading and text extraction"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_and_extract_text(self, pdf_url: str) -> Optional[List[str]]:
        """
        Download PDF from URL and extract text from each page
        
        Args:
            pdf_url: URL to the PDF file
            
        Returns:
            List of strings, each containing text from one page
        """
        try:
            # Download PDF
            logging.info(f"Downloading PDF from: {pdf_url}")
            response = self.session.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').lower() != 'application/pdf':
                logging.warning(f"Content type is not PDF: {response.headers.get('content-type')}")
            
            # Extract text using PyMuPDF
            pdf_document = fitz.open(stream=response.content, filetype="pdf")
            pages_text = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text = page.get_text()
                
                # Clean and normalize text
                cleaned_text = self._clean_text(text)
                pages_text.append(cleaned_text)
                
                logging.debug(f"Page {page_num + 1}: {len(cleaned_text)} characters")
            
            pdf_document.close()
            
            logging.info(f"Successfully extracted text from {len(pages_text)} pages")
            return pages_text
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading PDF: {str(e)}")
            raise Exception(f"Failed to download PDF: {str(e)}")
        
        except Exception as e:
            logging.error(f"Error processing PDF: {str(e)}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\.,!?;:()\-"\']', ' ', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text.strip()
    
    def validate_firebase_url(self, url: str) -> bool:
        """
        Validate if URL is a Firebase Storage URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid Firebase URL
        """
        try:
            parsed = urlparse(url)
            
            # Check for Firebase Storage patterns
            firebase_patterns = [
                'firebasestorage.googleapis.com',
                'firebase.google.com',
                'storage.googleapis.com'
            ]
            
            return any(pattern in parsed.netloc.lower() for pattern in firebase_patterns)
            
        except Exception:
            return False
    
    def get_pdf_metadata(self, pdf_url: str) -> Optional[Dict]:
        """
        Get basic metadata about the PDF
        
        Args:
            pdf_url: URL to the PDF file
            
        Returns:
            Dictionary with metadata or None if failed
        """
        try:
            response = self.session.head(pdf_url, timeout=10)
            response.raise_for_status()
            
            return {
                'content_length': response.headers.get('content-length'),
                'content_type': response.headers.get('content-type'),
                'last_modified': response.headers.get('last-modified'),
                'url': pdf_url
            }
            
        except Exception as e:
            logging.error(f"Error getting PDF metadata: {str(e)}")
            return None
