// PDF Analysis Tool - Client-side JavaScript

class PDFAnalyzer {
    constructor() {
        this.pdfLoaded = false;
        this.questionHistory = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkStatus();
    }

    bindEvents() {
        // PDF Upload Form
        document.getElementById('pdf-upload-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadPDF();
        });

        // Question Form
        document.getElementById('question-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.askQuestion();
        });

        // Clear Button
        document.getElementById('clear-btn').addEventListener('click', () => {
            this.clearSession();
        });

        // Auto-resize textarea
        const questionTextarea = document.getElementById('question');
        questionTextarea.addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
        });
    }

    async uploadPDF() {
        const urlInput = document.getElementById('pdf-url');
        const uploadBtn = document.getElementById('upload-btn');
        const pdfUrl = urlInput.value.trim();

        if (!pdfUrl) {
            this.showAlert('Please enter a PDF URL', 'danger');
            return;
        }

        // Validate URL format
        if (!this.isValidFirebaseURL(pdfUrl)) {
            this.showAlert('Please enter a valid Firebase Storage URL', 'danger');
            return;
        }

        this.setButtonLoading(uploadBtn, true);

        try {
            const response = await fetch('/upload_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ pdf_url: pdfUrl })
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert(result.message, 'success');
                this.pdfLoaded = true;
                this.updatePDFStatus(pdfUrl, result.total_pages);
                this.enableQuestionForm();
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showAlert('Failed to upload PDF. Please try again.', 'danger');
        } finally {
            this.setButtonLoading(uploadBtn, false);
        }
    }

    async askQuestion() {
        const questionInput = document.getElementById('question');
        const askBtn = document.getElementById('ask-btn');
        const question = questionInput.value.trim();

        if (!question) {
            this.showAlert('Please enter a question', 'danger');
            return;
        }

        if (!this.pdfLoaded) {
            this.showAlert('Please upload a PDF first', 'danger');
            return;
        }

        this.setButtonLoading(askBtn, true);

        try {
            const response = await fetch('/ask_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            });

            const result = await response.json();

            if (result.success) {
                this.displayAnswer(result.answer);
                this.addToHistory(question, result.answer);
                questionInput.value = '';
                questionInput.style.height = 'auto';
            } else {
                this.showAlert(result.error, 'warning');
            }
        } catch (error) {
            console.error('Question error:', error);
            this.showAlert('Failed to process question. Please try again.', 'danger');
        } finally {
            this.setButtonLoading(askBtn, false);
        }
    }

    async clearSession() {
        try {
            const response = await fetch('/clear_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (result.success) {
                this.resetUI();
                this.showAlert('Session cleared successfully', 'info');
            }
        } catch (error) {
            console.error('Clear error:', error);
            this.showAlert('Failed to clear session', 'danger');
        }
    }

    async checkStatus() {
        try {
            const response = await fetch('/status');
            const status = await response.json();

            if (status.pdf_loaded) {
                this.pdfLoaded = true;
                this.updatePDFStatus(status.pdf_url, status.total_pages);
                this.enableQuestionForm();
            }
        } catch (error) {
            console.error('Status check error:', error);
        }
    }

    displayAnswer(answer) {
        const answerSection = document.getElementById('answer-section');
        const answerContent = document.getElementById('answer-content');

        const confidenceClass = this.getConfidenceClass(answer.confidence);
        const confidenceText = this.getConfidenceText(answer.confidence);

        answerContent.innerHTML = `
            <div class="answer-content mb-3">
                <h6 class="mb-2">Answer:</h6>
                <p class="mb-0">${this.escapeHtml(answer.answer)}</p>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <h6>Page Reference:</h6>
                        <a href="${answer.page_link}" target="_blank" class="page-reference">
                            <i class="fas fa-external-link-alt"></i>
                            Page ${answer.page_number}
                        </a>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <h6>Confidence:</h6>
                        <span class="badge confidence-badge ${confidenceClass}">
                            ${confidenceText} (${(answer.confidence * 100).toFixed(1)}%)
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <h6>Text Excerpt:</h6>
                <div class="excerpt-text">
                    ${this.escapeHtml(answer.excerpt)}
                </div>
            </div>
        `;

        answerSection.classList.remove('d-none');
        answerSection.classList.add('fade-in');
        answerSection.scrollIntoView({ behavior: 'smooth' });
    }

    addToHistory(question, answer) {
        this.questionHistory.unshift({ question, answer, timestamp: new Date() });
        this.updateHistoryDisplay();
    }

    updateHistoryDisplay() {
        const historySection = document.getElementById('history-section');
        const historyContainer = document.getElementById('question-history');

        if (this.questionHistory.length === 0) {
            historySection.classList.add('d-none');
            return;
        }

        historyContainer.innerHTML = this.questionHistory
            .slice(0, 5) // Show last 5 questions
            .map(item => `
                <div class="question-history-item">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <strong>Q: ${this.escapeHtml(item.question)}</strong>
                        <small class="text-muted">${this.formatTime(item.timestamp)}</small>
                    </div>
                    <div class="text-muted">
                        <strong>A:</strong> ${this.escapeHtml(item.answer.answer)}
                        <span class="ms-2">
                            <a href="${item.answer.page_link}" target="_blank" class="text-primary">
                                <i class="fas fa-external-link-alt"></i> Page ${item.answer.page_number}
                            </a>
                        </span>
                    </div>
                </div>
            `).join('');

        historySection.classList.remove('d-none');
    }

    updatePDFStatus(pdfUrl, totalPages) {
        const statusElement = document.getElementById('pdf-status');
        const pageCountElement = document.getElementById('page-count');
        const pdfLinkElement = document.getElementById('pdf-link');

        pageCountElement.textContent = totalPages;
        pdfLinkElement.href = pdfUrl;

        statusElement.classList.remove('d-none');
        statusElement.classList.add('fade-in');
    }

    enableQuestionForm() {
        const askBtn = document.getElementById('ask-btn');
        const questionInput = document.getElementById('question');
        
        askBtn.disabled = false;
        questionInput.disabled = false;
        questionInput.focus();
    }

    resetUI() {
        this.pdfLoaded = false;
        this.questionHistory = [];
        
        // Reset forms
        document.getElementById('pdf-upload-form').reset();
        document.getElementById('question-form').reset();
        
        // Hide sections
        document.getElementById('pdf-status').classList.add('d-none');
        document.getElementById('answer-section').classList.add('d-none');
        document.getElementById('history-section').classList.add('d-none');
        
        // Disable question form
        document.getElementById('ask-btn').disabled = true;
        document.getElementById('question').disabled = true;
        
        // Clear alerts
        this.hideAlert();
    }

    setButtonLoading(button, loading) {
        const btnContent = button.querySelector('.btn-content');
        const spinner = button.querySelector('.spinner-border');
        const loadingText = button.querySelector('.loading-text');

        if (loading) {
            button.disabled = true;
            button.classList.add('btn-loading');
            btnContent.classList.add('d-none');
            spinner.classList.remove('d-none');
            loadingText.classList.remove('d-none');
        } else {
            button.disabled = false;
            button.classList.remove('btn-loading');
            btnContent.classList.remove('d-none');
            spinner.classList.add('d-none');
            loadingText.classList.add('d-none');
        }
    }

    showAlert(message, type) {
        const alertElement = document.getElementById('status-alert');
        const messageElement = document.getElementById('status-message');
        
        alertElement.className = `alert alert-${type} fade-in`;
        messageElement.textContent = message;
        alertElement.classList.remove('d-none');
        
        // Auto-hide success and info messages
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                this.hideAlert();
            }, 5000);
        }
    }

    hideAlert() {
        const alertElement = document.getElementById('status-alert');
        alertElement.classList.add('d-none');
    }

    isValidFirebaseURL(url) {
        const patterns = [
            /firebasestorage\.googleapis\.com/i,
            /firebase\.google\.com/i,
            /storage\.googleapis\.com/i
        ];
        
        return patterns.some(pattern => pattern.test(url));
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.7) return 'confidence-high';
        if (confidence >= 0.4) return 'confidence-medium';
        return 'confidence-low';
    }

    getConfidenceText(confidence) {
        if (confidence >= 0.7) return 'High';
        if (confidence >= 0.4) return 'Medium';
        return 'Low';
    }

    formatTime(timestamp) {
        return timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new PDFAnalyzer();
});
