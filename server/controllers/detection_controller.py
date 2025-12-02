"""Detection controller for handling book detection and OCR"""
from fastapi.responses import FileResponse
import cv2
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from services.detection_service import detection_service
from services.ocr_service import ocr_service
from services.agents_service import resolve_book_title
from utils.ocr_utils import clean_text, calculate_confidence, get_confidence_label

async def serve_crop(filename: str):
    """Serve crop images for debugging"""
    return FileResponse(os.path.join(config.DEBUG_CROPS_DIR, filename))

async def detect(conf: float = 0.6, iou: float = 0.5):
    """Detect books in uploaded image"""
    img = cv2.imread(config.UPLOAD_PATH)
    results = detection_service.predict(img, conf=conf, iou=iou)
    
    annotated = img.copy()
    for box, score, cls in zip(
        results.boxes.xyxy.cpu().numpy(),
        results.boxes.conf.cpu().numpy(),
        results.boxes.cls.cpu().numpy()
    ):
        x1, y1, x2, y2 = map(int, box)
        label = f"{results.names[int(cls)]} ({score:.2f})"
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(annotated, label, (x1, max(25, y1-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imwrite(config.DEBUG_IMG_PATH, annotated)
    return {
        "num_books": len(results.boxes),
        "original_image": "/debug_crops/original.jpg",
        "annotated_image": "/debug_crops/debug_image.jpg"
    }

async def detect_and_ocr(conf: float = 0.6, iou: float = 0.5):
    """Detect books with YOLO and run OCR on each detected book individually"""
    img = cv2.imread(config.UPLOAD_PATH)
    
    # Run YOLO detection
    results = detection_service.predict(img, conf=conf, iou=iou)
    
    if len(results.boxes) == 0:
        return {
            "num_books": 0,
            "books": [],
            "annotated_image": None
        }
    
    books_data = []
    annotated = img.copy()
    
    # Process each detected book
    for idx, (box, score, cls) in enumerate(zip(
        results.boxes.xyxy.cpu().numpy(),
        results.boxes.conf.cpu().numpy(),
        results.boxes.cls.cpu().numpy()
    )):
        x1, y1, x2, y2 = map(int, box)
        
        # Crop the book region
        book_crop = img[y1:y2, x1:x2]
        
        # Save crop for debugging
        crop_path = f"{config.DEBUG_CROPS_DIR}/book_{idx}.jpg"
        cv2.imwrite(crop_path, book_crop)
        
        # Run OCR on this specific book
        ocr_results = ocr_service.predict(book_crop)
        ocr_result = ocr_results[0] if ocr_results and len(ocr_results) > 0 else None
        
        # Process OCR results for this book
        cleaned_text = clean_text(ocr_result) if ocr_result else ""
        avg_confidence = calculate_confidence(ocr_result) if ocr_result else 0.0
        quality = get_confidence_label(avg_confidence)
        
        # Format detections for this book
        detections = []
        if ocr_result and 'rec_texts' in ocr_result:
            rec_texts = ocr_result['rec_texts']
            rec_scores = ocr_result['rec_scores']
            rec_polys = ocr_result['rec_polys']
            
            for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
                # Convert to absolute coordinates (add book crop offset to get original image coordinates)
                bbox_absolute = [[float(poly[i][0]) + x1, float(poly[i][1]) + y1] 
                                for i in range(len(poly))]
                # Also keep crop-relative coordinates for reference
                bbox_crop = [[float(poly[i][0]), float(poly[i][1])] 
                            for i in range(len(poly))]
                detections.append({
                    "text": text,
                    "confidence": round(score * 100, 2),
                    "bbox": bbox_absolute,  # Absolute coordinates in original image
                    "bbox_crop": bbox_crop  # Relative coordinates in book crop
                })
        
        # Store book data
        book_info = {
            "book_id": idx,
            "bbox": [int(x1), int(y1), int(x2), int(y2)],
            "detection_confidence": float(score),
            "class": results.names[int(cls)],
            "text": cleaned_text,
            "ocr_confidence": round(avg_confidence * 100, 2) if ocr_result else 0.0,
            "ocr_quality": quality,
            "num_text_detections": len(detections),
            "text_detections": detections,
            "crop_image": f"/debug_crops/book_{idx}.jpg"
        }
        books_data.append(book_info)
        
        # Draw on annotated image
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
        label = f"Book {idx}: {cleaned_text[:20]}..." if cleaned_text else f"Book {idx}"
        cv2.putText(annotated, label, (x1, max(25, y1-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Also draw OCR regions on the crop
        book_crop_annotated = book_crop.copy()
        if ocr_result and 'rec_polys' in ocr_result:
            rec_polys = ocr_result['rec_polys']
            for poly in rec_polys:
                # poly is already a numpy array with shape (4, 2)
                points = poly.astype(np.int32)
                cv2.polylines(book_crop_annotated, [points], True, (0, 255, 0), 2)
        
        crop_annotated_path = f"{config.DEBUG_CROPS_DIR}/book_{idx}_ocr.jpg"
        cv2.imwrite(crop_annotated_path, book_crop_annotated)
        book_info["crop_image_annotated"] = f"/debug_crops/book_{idx}_ocr.jpg"
    
    # Save overall annotated image
    annotated_path = f"{config.DEBUG_CROPS_DIR}/all_books_detected.jpg"
    cv2.imwrite(annotated_path, annotated)
    
    return {
        "num_books": len(results.boxes),
        "books": books_data,
        "annotated_image": "/debug_crops/all_books_detected.jpg",
        "original_image": "/debug_crops/original.jpg"
    }

async def detect_and_ocr_and_agent(conf: float = 0.6, iou: float = 0.5):
    """Detect books with YOLO, run OCR on each book, and resolve titles using agents"""
    img = cv2.imread(config.UPLOAD_PATH)
    
    # Run YOLO detection
    results = detection_service.predict(img, conf=conf, iou=iou)
    
    if len(results.boxes) == 0:
        return {
            "num_books": 0,
            "books": [],
            "annotated_image": None
        }
    
    books_data = []
    annotated = img.copy()
    
    # Process each detected book
    for idx, (box, score, cls) in enumerate(zip(
        results.boxes.xyxy.cpu().numpy(),
        results.boxes.conf.cpu().numpy(),
        results.boxes.cls.cpu().numpy()
    )):
        x1, y1, x2, y2 = map(int, box)
        
        # Crop the book region
        book_crop = img[y1:y2, x1:x2]
        
        # Save crop for debugging
        crop_path = f"{config.DEBUG_CROPS_DIR}/book_{idx}.jpg"
        cv2.imwrite(crop_path, book_crop)
        
        # Run OCR on this specific book
        try:
            ocr_results = ocr_service.predict(book_crop)
            ocr_result = ocr_results[0] if ocr_results and len(ocr_results) > 0 else None
        except (RuntimeError, AttributeError, Exception) as e:
            if "not available" in str(e) or (hasattr(ocr_service, '_available') and not ocr_service._available):
                print(f"⚠️  OCR not available for book {idx}: {e}")
                ocr_result = None
            else:
                raise
        
        # Process OCR results for this book
        cleaned_text = clean_text(ocr_result) if ocr_result else ""
        avg_confidence = calculate_confidence(ocr_result) if ocr_result else 0.0
        quality = get_confidence_label(avg_confidence)
        
        # Run agent to resolve book title
        agent_result = None
        if cleaned_text:
            try:
                # resolve_book_title will use config defaults if not provided
                agent_result = resolve_book_title(cleaned_text)
            except Exception as e:
                print(f"⚠️  Error in agent resolution for book {idx}: {e}")
                agent_result = {
                    "resolved_title": cleaned_text,
                    "confidence": 0.0,
                    "reasoning": f"Agent error: {str(e)}"
                }
        else:
            agent_result = {
                "resolved_title": "",
                "confidence": 0.0,
                "reasoning": "No OCR text to resolve"
            }
        
        # Format detections for this book
        detections = []
        if ocr_result and 'rec_texts' in ocr_result:
            rec_texts = ocr_result['rec_texts']
            rec_scores = ocr_result['rec_scores']
            rec_polys = ocr_result['rec_polys']
            
            for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
                # Convert to absolute coordinates (add book crop offset to get original image coordinates)
                bbox_absolute = [[float(poly[i][0]) + x1, float(poly[i][1]) + y1] 
                                for i in range(len(poly))]
                # Also keep crop-relative coordinates for reference
                bbox_crop = [[float(poly[i][0]), float(poly[i][1])] 
                            for i in range(len(poly))]
                detections.append({
                    "text": text,
                    "confidence": round(score * 100, 2),
                    "bbox": bbox_absolute,  # Absolute coordinates in original image
                    "bbox_crop": bbox_crop  # Relative coordinates in book crop
                })
        
        # Store book data with agent results
        book_info = {
            "book_id": idx,
            "bbox": [int(x1), int(y1), int(x2), int(y2)],
            "detection_confidence": float(score),
            "class": results.names[int(cls)],
            "text": cleaned_text,  # Original OCR text
            "ocr_confidence": round(avg_confidence * 100, 2) if ocr_result else 0.0,
            "ocr_quality": quality,
            "num_text_detections": len(detections),
            "text_detections": detections,
            "crop_image": f"/debug_crops/book_{idx}.jpg",
            # Agent results (LangGraph LLM agent + Google Books verification)
            "resolved_title": agent_result.get("resolved_title", ""),
            "agent_confidence": round(agent_result.get("confidence", 0.0) * 100, 2),
            "agent_reasoning": agent_result.get("reasoning", ""),
            "google_books_found": agent_result.get("google_books_found", False),
            "google_books_info": agent_result.get("google_books_info"),
            "google_books_verification": agent_result.get("google_books_verification", ""),
        }
        books_data.append(book_info)
        
        # Draw on annotated image with resolved title
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
        # Use resolved title if available, otherwise use OCR text
        display_text = agent_result.get("resolved_title", "") or cleaned_text
        label = f"Book {idx}: {display_text[:30]}..." if display_text else f"Book {idx}"
        cv2.putText(annotated, label, (x1, max(25, y1-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Also draw OCR regions on the crop
        book_crop_annotated = book_crop.copy()
        if ocr_result and 'rec_polys' in ocr_result:
            rec_polys = ocr_result['rec_polys']
            for poly in rec_polys:
                # poly is already a numpy array with shape (4, 2)
                points = poly.astype(np.int32)
                cv2.polylines(book_crop_annotated, [points], True, (0, 255, 0), 2)
        
        crop_annotated_path = f"{config.DEBUG_CROPS_DIR}/book_{idx}_ocr.jpg"
        cv2.imwrite(crop_annotated_path, book_crop_annotated)
        book_info["crop_image_annotated"] = f"/debug_crops/book_{idx}_ocr.jpg"
    
    # Save overall annotated image
    annotated_path = f"{config.DEBUG_CROPS_DIR}/all_books_detected.jpg"
    cv2.imwrite(annotated_path, annotated)
    
    return {
        "num_books": len(results.boxes),
        "books": books_data,
        "annotated_image": "/debug_crops/all_books_detected.jpg",
        "original_image": "/debug_crops/original.jpg"
    }

