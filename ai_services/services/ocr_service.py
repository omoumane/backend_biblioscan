"""OCR service for text recognition"""
import sys
import os

# IMPORTANT: Patch langchain.docstore BEFORE any other imports
# This must happen before PaddleOCR tries to import it
from types import ModuleType

# Create mock langchain modules for PaddleOCR compatibility
# PaddleOCR/paddlex requires old langchain modules that don't exist in newer versions
def _create_mock_langchain_modules():
    """Create mock langchain modules that PaddleOCR needs"""
    # Create docstore module
    if 'langchain.docstore' not in sys.modules:
        docstore_pkg = ModuleType('langchain.docstore')
        sys.modules['langchain.docstore'] = docstore_pkg
        
        document_module = ModuleType('langchain.docstore.document')
        class Document:
            def __init__(self, page_content="", metadata=None):
                self.page_content = page_content
                self.metadata = metadata or {}
        document_module.Document = Document
        sys.modules['langchain.docstore.document'] = document_module
        docstore_pkg.document = document_module
    
    # Create text_splitter module
    if 'langchain.text_splitter' not in sys.modules:
        text_splitter_module = ModuleType('langchain.text_splitter')
        sys.modules['langchain.text_splitter'] = text_splitter_module
        
        # Add basic TextSplitter classes
        class TextSplitter:
            def __init__(self, **kwargs):
                pass
            def split_text(self, text):
                return [text]
        
        class RecursiveCharacterTextSplitter(TextSplitter):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
        
        text_splitter_module.TextSplitter = TextSplitter
        text_splitter_module.CharacterTextSplitter = TextSplitter
        text_splitter_module.RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter

# Create the mock modules
::_create_mock_langchain_modules()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class OCRService:
    """Service for handling OCR operations"""
    
    def __init__(self):
        # Lazy import to avoid issues at module load time
        try:
            from paddleocr import PaddleOCR
            print(" Initialisation PaddleOCR...")
            self.ocr = PaddleOCR(
                lang=config.OCR_LANGUAGE,
                use_textline_orientation=True,  # Handles rotated text (important for book spines)
            )
            print(f" PaddleOCR chargé (GPU: {config.DEVICE == 'cuda'}, Lang: {config.OCR_LANGUAGE})")
            self._available = True
        except (ImportError, ModuleNotFoundError) as e:
            error_msg = str(e)
            if "No module named 'paddle'" in error_msg:
                print(f" ⚠️  PaddleOCR not available: PaddlePaddle is not installed.")
                print(f"     Note: PaddlePaddle may not support this Python version. Please install paddlepaddle manually.")
            else:
                print(f" ⚠️  PaddleOCR not available: {e}")
            self.ocr = None
            self._available = False
        except Exception as e:
            print(f" ⚠️  PaddleOCR initialization error: {e}")
            import traceback
            traceback.print_exc()
            self.ocr = None
            self._available = False
    
    def predict(self, image):
        """
        Run OCR prediction on an image.

        Retourne un dict au format :
        {
            "rec_texts": [ "text1", "text2", ... ],
            "rec_scores": [ 0.98, 0.91, ... ],
            "rec_polys": [ [[x1,y1],...], ... ]
        }
        """
        if not self._available or self.ocr is None:
            raise RuntimeError("PaddleOCR is not available. Please install required dependencies.")
        
        # Appel PaddleOCR
        result = self.ocr.ocr(image, cls=True)

        rec_texts = []
        rec_scores = []
        rec_polys = []

        if result is None:
            # Sécurité maximale : aucun texte
            print("⚠ PaddleOCR a retourné None")
            return {
                "rec_texts": [],
                "rec_scores": [],
                "rec_polys": [],
            }

        # result est typiquement : [ [ [box, (text, score)], ... ] ]
        for line in result or []:
            if not line:
                continue
            # line doit être une liste de items
            for item in (line or []):
                # item = [box, (text, score)]
                if not item or len(item) < 2:
                    continue
                box = item[0]
                rec = item[1]

                if box is None or rec is None:
                    continue

                # rec = (text, score)
                if not isinstance(rec, (list, tuple)) or len(rec) < 2:
                    continue

                text, score = rec[0], rec[1]

                # Filtre minimal
                if text is None:
                    continue

                try:
                    score_f = float(score)
                except Exception:
                    score_f = 0.0

                rec_polys.append(box)
                rec_texts.append(str(text))
                rec_scores.append(score_f)

        return {
            "rec_texts": rec_texts,
            "rec_scores": rec_scores,
            "rec_polys": rec_polys,
        }


# Global OCR service instance
try:
    ocr_service = OCRService()
except Exception as e:
    print(f" ⚠️  Warning: Could not initialize OCR service: {e}")
    # Create a dummy instance to prevent import errors
    ocr_service = OCRService()
    ocr_service._available = False
