import os
import logging
from flask import (
    Flask, render_template, request,
    jsonify
)
from pdf_processor import PDFProcessor
from question_answering import QuestionAnswering

# ─── Flask Setup ───────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# ─── In-Memory Globals ─────────────────────────────────────────────────────────
pdf_processor   = None
qa_system       = None
current_pdf_url = None

# ─── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    global pdf_processor, qa_system, current_pdf_url

    data    = request.get_json(silent=True) or {}
    pdf_url = (data.get('pdf_url') or '').strip()

    if not pdf_url:
        return jsonify(success=False, error="PDF URL is required"), 400

    if 'firebase' not in pdf_url.lower() and 'googleapis.com' not in pdf_url.lower():
        return jsonify(success=False, error="Invalid Firebase Storage URL"), 400

    logging.info(f"Downloading & processing PDF from {pdf_url}")
    processor = PDFProcessor()
    pages = processor.download_and_process_pdf(pdf_url)
    if not pages:
        return jsonify(success=False, error="Failed to extract text from PDF"), 500

    # store in globals
    pdf_processor   = processor
    qa_system       = QuestionAnswering(pages)
    current_pdf_url = pdf_url
    total = len(pages)

    logging.info(f"Loaded {total} pages")
    return jsonify(
        success=True,
        message=f"PDF processed successfully! {total} pages loaded.",
        total_pages=total
    )


@app.route('/ask_question', methods=['POST'])
def ask_question():
    global qa_system, current_pdf_url

    data     = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()

    if not question:
        return jsonify(success=False, error="Question is required"), 400

    if qa_system is None:
        return jsonify(success=False, error="Please upload a PDF first"), 400

    logging.info(f"Answering: {question!r}")
    result = qa_system.find_answer(question)

    if not result:
        return jsonify(
            success=True,
            answer="No relevant answer found in the PDF.",
            page_number=None,
            confidence=0,
            pdf_link=current_pdf_url
        )

    page_link = f"{current_pdf_url}#page={result['page_number']}"
    return jsonify(
        success=True,
        answer=result['answer'],
        page_number=result['page_number'],
        confidence=result['confidence'],
        pdf_link=page_link
    )


@app.route('/status')
def status():
    """Called on page load to see if a PDF has already been uploaded."""
    loaded = qa_system is not None
    total  = len(pdf_processor.get_pages_data()) if loaded else 0
    return jsonify(
        pdf_loaded=loaded,
        total_pages=total,
        pdf_url=current_pdf_url or ""
    )


# ─── Start App ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
