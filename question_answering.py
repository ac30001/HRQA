import difflib
import logging
import re
from typing import List, Dict, Optional, Tuple

class QuestionAnswering:
    """Handles question answering using fuzzy text matching"""
    
    def __init__(self):
        self.min_confidence = 0.1  # Minimum confidence threshold
        self.context_window = 200  # Characters around the match to include
    
    def answer_question(self, question: str, pdf_pages: List[str]) -> Optional[Dict]:
        """
        Find the best answer to a question in the PDF pages
        
        Args:
            question: User's question
            pdf_pages: List of text from each PDF page
            
        Returns:
            Dictionary with answer, page number, confidence, and excerpt
        """
        try:
            # Preprocess question
            processed_question = self._preprocess_text(question)
            question_keywords = self._extract_keywords(processed_question)
            
            logging.info(f"Processing question: {question}")
            logging.info(f"Extracted keywords: {question_keywords}")
            
            best_match = None
            best_confidence = 0
            best_page = 0
            best_excerpt = ""
            
            # Search through each page
            for page_num, page_text in enumerate(pdf_pages):
                if not page_text.strip():
                    continue
                
                # Find matches on this page
                matches = self._find_matches(question_keywords, page_text)
                
                for match in matches:
                    confidence = self._calculate_confidence(
                        processed_question, 
                        match['text'], 
                        question_keywords
                    )
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_page = page_num + 1  # 1-indexed
                        best_excerpt = match['excerpt']
                        best_match = match
            
            # Check if we found a good enough match
            if best_confidence < self.min_confidence:
                logging.info(f"No good match found. Best confidence: {best_confidence}")
                return None
            
            # Generate answer
            answer = self._generate_answer(best_match, processed_question)
            
            result = {
                'answer': answer,
                'page_number': best_page,
                'confidence': round(best_confidence, 3),
                'excerpt': best_excerpt,
                'question': question
            }
            
            logging.info(f"Found answer with confidence {best_confidence:.3f} on page {best_page}")
            return result
            
        except Exception as e:
            logging.error(f"Error in question answering: {str(e)}")
            return None
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better matching"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'what', 'how', 'when', 'where', 'why', 'who',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'shall', 'this', 'that', 'these', 'those'
        }
        
        words = text.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words 
                   if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def _find_matches(self, keywords: List[str], page_text: str) -> List[Dict]:
        """Find potential matches in page text"""
        matches = []
        processed_text = self._preprocess_text(page_text)
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', processed_text)
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            # Count keyword matches in sentence
            keyword_count = sum(1 for keyword in keywords if keyword in sentence)
            
            if keyword_count > 0:
                # Get surrounding context
                start_idx = max(0, i - 1)
                end_idx = min(len(sentences), i + 2)
                context_sentences = sentences[start_idx:end_idx]
                
                # Create excerpt from original text
                excerpt = self._create_excerpt(sentence, page_text)
                
                matches.append({
                    'text': sentence,
                    'excerpt': excerpt,
                    'keyword_count': keyword_count,
                    'context': ' '.join(context_sentences)
                })
        
        return matches
    
    def _calculate_confidence(self, question: str, answer_text: str, keywords: List[str]) -> float:
        """Calculate confidence score for a match"""
        # Keyword overlap score
        keyword_score = 0
        for keyword in keywords:
            if keyword in answer_text:
                keyword_score += 1
        
        keyword_ratio = keyword_score / len(keywords) if keywords else 0
        
        # Similarity score using difflib
        similarity = difflib.SequenceMatcher(None, question, answer_text).ratio()
        
        # Length penalty for very short matches
        length_penalty = min(1.0, len(answer_text) / 50)
        
        # Combined confidence score
        confidence = (keyword_ratio * 0.5 + similarity * 0.3 + length_penalty * 0.2)
        
        return confidence
    
    def _create_excerpt(self, sentence: str, full_text: str) -> str:
        """Create a contextual excerpt around the matched sentence"""
        # Find the sentence in the original text
        sentence_clean = sentence.strip()
        
        # Simple approach: find similar text and get context
        words = sentence_clean.split()[:5]  # First 5 words
        search_phrase = ' '.join(words)
        
        # Find in original text (case insensitive)
        text_lower = full_text.lower()
        search_lower = search_phrase.lower()
        
        pos = text_lower.find(search_lower)
        
        if pos == -1:
            # Fallback to just the sentence
            return sentence[:200] + "..." if len(sentence) > 200 else sentence
        
        # Get context around the match
        start = max(0, pos - self.context_window)
        end = min(len(full_text), pos + len(search_phrase) + self.context_window)
        
        excerpt = full_text[start:end].strip()
        
        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(full_text):
            excerpt = excerpt + "..."
        
        return excerpt
    
    def _generate_answer(self, match: Dict, question: str) -> str:
        """Generate a natural language answer"""
        # Simple answer generation based on the match
        answer_text = match['text']
        
        # Clean up the answer
        answer_text = answer_text.strip()
        
        # Capitalize first letter
        if answer_text:
            answer_text = answer_text[0].upper() + answer_text[1:]
        
        # Ensure it ends with punctuation
        if answer_text and answer_text[-1] not in '.!?':
            answer_text += '.'
        
        return answer_text
