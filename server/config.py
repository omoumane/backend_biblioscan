"""Configuration settings for the BiblioScan server"""
import os
import torch

# =========================================================
#  PATHS
# =========================================================
MODEL_PATH = "./models/bookshelf_best.pt"
UPLOAD_PATH = "uploaded.jpg"
DEBUG_CROPS_DIR = "debug_crops"
DEBUG_IMG_PATH = f"{DEBUG_CROPS_DIR}/debug_image.jpg"
ORIGINAL_PATH = f"{DEBUG_CROPS_DIR}/original.jpg"

# Create debug directory if it doesn't exist
os.makedirs(DEBUG_CROPS_DIR, exist_ok=True)

# =========================================================
#  DEVICE CONFIGURATION
# =========================================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =========================================================
#  OCR CONFIGURATION
# =========================================================
OCR_LANGUAGE = 'fr'  # English (works well for most Latin-based languages)

# =========================================================
#  YOLO CONFIGURATION
# =========================================================
DEFAULT_CONF = 0.6
DEFAULT_IOU = 0.5
DEFAULT_IMGSZ = 640

# =========================================================
#  LLM CONFIGURATION (for agents)
# =========================================================
# LLM provider: "openai" or "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
# Model name (e.g., "gpt-4o-mini" for OpenAI, "llama3.2" for Ollama)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
# OpenAI API key (optional, can be set via environment variable)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

