from ultralytics import YOLO
import cv2

MODEL_PATH = "./models/bookshelf_best.pt"
IMAGE_PATH = "uploaded.jpg"  # ou "test.jpg" si tu préfères

print("Chargement du modèle...")
model = YOLO(MODEL_PATH)

print("Lecture de l'image...")
img = cv2.imread(IMAGE_PATH)
if img is None:
    raise SystemExit(f"❌ Impossible de lire l'image : {IMAGE_PATH}")

print("Shape image :", img.shape)

print("Prédiction YOLO...")
results = model.predict(img, conf=0.1, iou=0.5, imgsz=640, verbose=True)[0]

print("\n=== Résumé YOLO ===")
print("Nombre de boxes :", len(results.boxes))

if len(results.boxes) > 0:
    print("Boxes :", results.boxes.xyxy.cpu().numpy())
    print("Scores:", results.boxes.conf.cpu().numpy())
    annotated = results.plot()
    cv2.imwrite("debug_yolo.jpg", annotated)
    print("✅ Image annotée sauvegardée sous debug_yolo.jpg")
else:
    print("❌ Aucune box détectée par YOLO")
