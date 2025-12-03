"""Detection service for book detection using YOLO"""
from ultralytics import YOLO
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class DetectionService:
    """Service for handling book detection"""
    
    def __init__(self):
        print(f" Device : {config.DEVICE}")
        self.model = YOLO(config.MODEL_PATH)
        self.model.to(config.DEVICE)
        print(f" YOLO chargé depuis {config.MODEL_PATH}")
    
    def predict(self, image, conf=None, iou=None, imgsz=None):
        """Run YOLO detection on an image"""
        conf = conf or config.DEFAULT_CONF
        iou = iou or config.DEFAULT_IOU
        imgsz = imgsz or config.DEFAULT_IMGSZ
        return self.model.predict(
            image, 
            conf=conf, 
            iou=iou, 
            imgsz=imgsz, 
            device=config.DEVICE, 
            verbose=False
        )[0]

# Global detection service instance
detection_service = DetectionService()

