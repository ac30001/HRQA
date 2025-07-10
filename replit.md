# PDF Analysis Tool

## Overview

This is a Flask-based web application that allows users to upload PDF files from Firebase Storage URLs, extract text content, and ask questions about the documents using fuzzy text matching. The application provides a simple interface for document analysis and question-answering without requiring complex NLP models.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Session Management**: Flask sessions with secret key configuration
- **Text Processing**: PyMuPDF (fitz) for PDF text extraction
- **Question Answering**: Custom fuzzy text matching algorithm using difflib
- **HTTP Client**: Requests library for PDF downloads

### Frontend Architecture
- **Templates**: Jinja2 templating engine with Bootstrap 5 for responsive UI
- **JavaScript**: Vanilla JavaScript class-based approach for client-side interactions
- **Styling**: Bootstrap 5 with custom CSS overrides and Font Awesome icons

### Data Storage
- **Session Storage**: Flask sessions for temporary storage of PDF content and user data
- **No Persistent Database**: All data is stored in memory/session during user interaction

## Key Components

### PDFProcessor Class
- **Purpose**: Handles PDF downloading from URLs and text extraction
- **Key Methods**:
  - `download_and_extract_text()`: Downloads PDF from URL and extracts text per page
  - `_clean_text()`: Normalizes extracted text content
- **Dependencies**: PyMuPDF, requests

### QuestionAnswering Class
- **Purpose**: Implements fuzzy text matching for answering user questions
- **Key Methods**:
  - `answer_question()`: Finds best matching content for user questions
  - `_find_matches()`: Searches for keyword matches across PDF pages
  - `_calculate_confidence()`: Scores match quality
- **Algorithm**: Keyword extraction + fuzzy matching with confidence scoring

### Flask Routes
- **`/`**: Renders main interface template
- **`/upload_pdf`**: Handles PDF URL processing and text extraction
- **`/ask_question`**: Processes user questions and returns answers

### Frontend Components
- **PDFAnalyzer Class**: Manages client-side interactions
- **Event Handlers**: Form submissions, status updates, session management
- **UI Features**: Loading states, confidence badges, question history

## Data Flow

1. **PDF Upload**: User provides Firebase Storage URL
2. **PDF Processing**: Server downloads PDF and extracts text per page
3. **Session Storage**: PDF content stored in Flask session
4. **Question Processing**: User asks questions about PDF content
5. **Text Matching**: System searches for relevant content using fuzzy matching
6. **Response Generation**: Best matches returned with confidence scores and page references

## External Dependencies

### Python Libraries
- **Flask**: Web framework and routing
- **PyMuPDF (fitz)**: PDF text extraction
- **requests**: HTTP client for PDF downloads
- **difflib**: Text similarity matching
- **urllib.parse**: URL validation and parsing

### Frontend Dependencies
- **Bootstrap 5**: UI framework via CDN
- **Font Awesome 6**: Icons via CDN
- **Vanilla JavaScript**: No external JS frameworks

### External Services
- **Firebase Storage**: PDF file hosting (user-provided URLs)

## Deployment Strategy

### Environment Configuration
- **Development**: Flask debug mode enabled
- **Production**: Secret key via environment variable `SESSION_SECRET`
- **Host Configuration**: Configured for 0.0.0.0:5000

### File Structure
```
├── app.py              # Main Flask application
├── main.py             # Application entry point
├── pdf_processor.py    # PDF processing logic
├── question_answering.py # QA system implementation
├── static/
│   ├── script.js       # Client-side JavaScript
│   └── style.css       # Custom styles
└── templates/
    └── index.html      # Main UI template
```

### Security Considerations
- URL validation for Firebase Storage endpoints
- Session-based data isolation
- Input sanitization and error handling
- Request timeouts for external PDF downloads

### Scalability Limitations
- Session-based storage limits concurrent users
- In-memory text processing may not scale for large documents
- No persistent storage for user data or document cache

### Deployment Requirements
- Python 3.x environment
- Flask and dependencies installed
- Network access for Firebase Storage URLs
- Sufficient memory for PDF text processing