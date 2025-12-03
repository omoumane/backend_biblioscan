"""OCR service for text recognition"""
import sys
import os
import numpy as np

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
_create_mock_langchain_modules()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Fix for PaddleOCR compatibility with newer langchain versions
def _patch_langchain_docstore():
    """Patch langchain.docstore for PaddleOCR compatibility"""
    try:
        from types import ModuleType
        
        # Create the docstore module structure
        docstore_module = ModuleType('langchain.docstore')
        
        # Create a Document class that paddlex expects
        class Document:
            def __init__(self, page_content="", metadata=None):
                self.page_content = page_content
                self.metadata = metadata or {}
        
        # Add Document to the module
        docstore_module.Document = Document
        docstore_module.document = Document
        
        # Register in sys.modules BEFORE any imports
        sys.modules['langchain.docstore'] = docstore_module
        sys.modules['langchain.docstore.document'] = Document
        
        # Also try to add to langchain if it exists
        try:
            import langchain
            langchain.docstore = docstore_module
        except:
            pass
            
    except Exception as e:
        # If patching fails, continue anyway
        pass

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
                print(f"     Note: PaddlePaddle may not support Python 3.14. Please use Python 3.11 or install paddlepaddle manually.")
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

        if not self._available or self.ocr is None:
            raise RuntimeError("PaddleOCR is not available. Please install required dependencies.")

        result = self.ocr.ocr(image, cls=True)

        rec_texts = []
        rec_scores = []
        rec_polys = []

        for line in result:
            for item in line:
                try:
                    box, (text, score) = item
                    rec_polys.append(np.array(box, dtype=np.float32))
                    rec_texts.append(text)
                    rec_scores.append(float(score))
                except Exception:
                    continue

        return [{
            "rec_texts": rec_texts,
            "rec_scores": rec_scores,
            "rec_polys": rec_polys,
            "raw": result,
        }]



try:
    ocr_service = OCRService()
except Exception as e:
    print(f" ⚠️  Warning: Could not initialize OCR service: {e}")
    # Create a dummy instance to prevent import errors
    ocr_service = OCRService()
    ocr_service._available = False

