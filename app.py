import os
import logging
from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from pdf_processor import PDFProcessor
from question_answering import QuestionAnswering

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize processors
pdf_processor = PDFProcessor()
qa_system = QuestionAnswering()

@app.route('/')
def index():
    """Main page with PDF upload and question interface"""
    return render_template('index.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF URL upload and processing"""
    try:
        data = request.get_json()
        pdf_url = data.get('pdf_url', '').strip()
        
        if not pdf_url:
            return jsonify({'success': False, 'error': 'PDF URL is required'}), 400
        
        # Validate Firebase URL format
        if not ('firebase' in pdf_url.lower() or 'googleapis.com' in pdf_url.lower()):
            return jsonify({'success': False, 'error': 'Please provide a valid Firebase Storage URL'}), 400
        
        # Process PDF
        logging.info(f"Processing PDF from URL: {pdf_url}")
        pdf_text = pdf_processor.download_and_extract_text(pdf_url)
        
        if not pdf_text:
            return jsonify({'success': False, 'error': 'Failed to extract text from PDF'}), 400
        
        # Store in session
        session['pdf_url'] = pdf_url
        session['pdf_text'] = pdf_text
        session['total_pages'] = len(pdf_text)
        
        logging.info(f"Successfully processed PDF with {len(pdf_text)} pages")
        
        return jsonify({
            'success': True,
            'message': f'PDF processed successfully! Found {len(pdf_text)} pages.',
            'total_pages': len(pdf_text)
        })
        
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        return jsonify({'success': False, 'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/ask_question', methods=['POST'])
def ask_question():
    """Handle question answering"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Question is required'}), 400
        
        # Check if PDF is loaded
        if 'pdf_text' not in session:
            return jsonify({'success': False, 'error': 'Please upload a PDF first'}), 400
        
        pdf_text = session['pdf_text']
        pdf_url = session['pdf_url']
        
        # Get answer from QA system
        logging.info(f"Answering question: {question}")
        result = qa_system.answer_question(question, pdf_text)
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Could not find a relevant answer in the PDF'
            }), 400
        
        # Add page link
        page_link = f"{pdf_url}#page={result['page_number']}"
        result['page_link'] = page_link
        
        logging.info(f"Found answer on page {result['page_number']} with confidence {result['confidence']:.2f}")
        
        return jsonify({
            'success': True,
            'answer': result
        })
        
    except Exception as e:
        logging.error(f"Error answering question: {str(e)}")
        return jsonify({'success': False, 'error': f'Error answering question: {str(e)}'}), 500

@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Clear the current session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Session cleared successfully'})

@app.route('/status')
def status():
    """Get current session status"""
    pdf_loaded = 'pdf_text' in session
    total_pages = session.get('total_pages', 0) if pdf_loaded else 0
    
    return jsonify({
        'pdf_loaded': pdf_loaded,
        'total_pages': total_pages,
        'pdf_url': session.get('pdf_url', '') if pdf_loaded else ''
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
