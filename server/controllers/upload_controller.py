"""Upload controller for handling image uploads"""
from fastapi import File, UploadFile
import cv2
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

async def upload_image(file: UploadFile = File(...)):
    """Handle image upload"""
    content = await file.read()
    with open(config.UPLOAD_PATH, "wb") as f:
        f.write(content)
    img = cv2.imread(config.UPLOAD_PATH)
    cv2.imwrite(config.ORIGINAL_PATH, img)
    return {"message": " Image uploadée avec succès", "path": config.UPLOAD_PATH}

