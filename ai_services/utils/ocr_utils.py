"""OCR utility functions"""
def clean_text(ocr_result):
    """Clean and format OCR text from PaddleOCR result"""
    if not ocr_result or 'rec_texts' not in ocr_result:
        return ""
    texts = ocr_result['rec_texts']
    if not texts:
        return ""
    text = ' '.join(texts)
    text = ' '.join(text.split())
    text = text.title()
    return text

def calculate_confidence(ocr_result):
    """Calculate average confidence from PaddleOCR result"""
    if not ocr_result or 'rec_scores' not in ocr_result:
        return 0.0
    confidences = ocr_result['rec_scores']
    if not confidences:
        return 0.0
    return sum(confidences) / len(confidences)

def get_confidence_label(confidence):
    """Get quality label based on confidence score"""
    if confidence >= 0.9:
        return "Excellent"
    elif confidence >= 0.7:
        return "Good"
    elif confidence >= 0.5:
        return "Fair"
    else:
        return "Poor"

