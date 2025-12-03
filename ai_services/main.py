from typing import List

from fastapi import FastAPI, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import uvicorn
import mysql.connector

from controllers import upload_controller, detection_controller

# =========================================================
#  APP CONFIGURATION
# =========================================================
app = FastAPI(
    title="BiblioScan Détection Serveur",
    version="1.1",
    description=(
        "API FastAPI pour l'upload d'images de bibliothèques, la détection de livres "
        "avec YOLO, l'OCR et les agents LLM (résolution de titres)."
    ),
    contact={"name": "BiblioScan"},
    license_info={"name": "Propriétaire (usage interne)"},
    openapi_tags=[
        {"name": "Upload", "description": "Upload d'images à analyser."},
        {"name": "Détection", "description": "Détection YOLO sur l'image."},
        {"name": "OCR", "description": "OCR par livre détecté."},
        {"name": "Agents", "description": "Agents LLM pour résoudre les titres."},
        {"name": "Debug", "description": "Servir les images de debug / crops."},
        {
            "name": "Biblio",
            "description": "Scan d’une étagère et insertion en base de données.",
        },
    ],
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
#  BASE DE DONNÉES
# =========================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "bibliodb",
}


def insert_book(golden_record: dict, biblio_id: int, ligne: int, col: int) -> None:
    """Insertion d’un livre dans la table `livres`."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
        INSERT INTO livres
          (biblio_id, titre, auteur, date_pub,
           position_ligne, position_colonne,
           couverture_url, isbn)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(
            sql,
            (
                biblio_id,
                golden_record.get("titre"),
                golden_record.get("auteur"),
                golden_record.get("date_pub"),
                ligne,
                col,
                golden_record.get("cover"),
                golden_record.get("isbn"),
            ),
        )

        conn.commit()
        print("✅ Livre inséré en BD :", golden_record.get("titre"))

    except Exception as e:
        print("❌ Erreur insertion BD :", e)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


# =========================================================
#  SCHÉMAS Pydantic (OpenAPI)
# =========================================================
class UploadResponse(BaseModel):
    message: str = Field(
        ...,
        description="Message de confirmation après upload.",
        json_schema_extra={"example": "Image uploadée avec succès"},
    )
    path: str = Field(
        ...,
        description="Chemin du fichier image stocké côté serveur.",
        json_schema_extra={"example": "uploaded.jpg"},
    )


class TextDetection(BaseModel):
    text: str = Field(..., json_schema_extra={"example": "Deep Learning"})
    confidence: float = Field(
        ...,
        description="Confiance OCR en pourcentage (0-100).",
        json_schema_extra={"example": 97.32},
    )
    bbox: List[List[float]] = Field(
        ...,
        description="Polygone de la boîte englobante dans l'image originale.",
        json_schema_extra={
            "example": [[12.0, 34.0], [56.0, 34.0], [56.0, 78.0], [12.0, 78.0]]
        },
    )
    bbox_crop: List[List[float]] = Field(
        ...,
        description="Polygone de la boîte englobante dans le crop du livre.",
        json_schema_extra={
            "example": [[0.0, 0.0], [44.0, 0.0], [44.0, 40.0], [0.0, 40.0]]
        },
    )


class BookOCR(BaseModel):
    book_id: int = Field(..., json_schema_extra={"example": 0})
    bbox: List[int] = Field(
        ...,
        description="[x1, y1, x2, y2] dans l'image originale.",
        json_schema_extra={"example": [10, 20, 200, 300]},
    )
    detection_confidence: float = Field(
        ...,
        description="Confiance YOLO (0-1).",
        json_schema_extra={"example": 0.93},
    )
    class_name: str = Field(
        ...,
        alias="class",
        description="Classe détectée par YOLO.",
        json_schema_extra={"example": "book"},
    )
    text: str = Field(
        ...,
        description="Texte OCR nettoyé pour ce livre.",
        json_schema_extra={"example": "Deep Learning with Python"},
    )
    ocr_confidence: float = Field(
        ...,
        description="Confiance moyenne OCR en pourcentage (0-100).",
        json_schema_extra={"example": 89.5},
    )
    ocr_quality: str = Field(
        ...,
        description="excellent / good / fair / poor",
        json_schema_extra={"example": "excellent"},
    )
    num_text_detections: int = Field(
        ...,
        description="Nombre de régions de texte détectées.",
        json_schema_extra={"example": 4},
    )
    text_detections: List[TextDetection]
    crop_image: str = Field(
        ...,
        description="Chemin vers l'image crop du livre.",
        json_schema_extra={"example": "/debug_crops/book_0.jpg"},
    )
    crop_image_annotated: str | None = Field(
        None,
        description="Chemin vers le crop annoté avec les régions OCR.",
        json_schema_extra={"example": "/debug_crops/book_0_ocr.jpg"},
    )

    model_config = ConfigDict(validate_by_name=True)


class BookWithAgent(BookOCR):
    resolved_title: str = Field(
        ...,
        description="Titre final résolu par l'agent.",
        json_schema_extra={"example": "Deep Learning with Python, 2nd Edition"},
    )
    agent_confidence: float = Field(
        ...,
        description="Confiance de l'agent en pourcentage (0-100).",
        json_schema_extra={"example": 95.0},
    )
    agent_reasoning: str = Field(
        ...,
        description="Raisonnement textuel de l'agent.",
        json_schema_extra={
            "example": "L'OCR contient 'Deep Learning' et 'Python', croisé avec Google Books."
        },
    )
    google_books_found: bool = Field(
        ...,
        description="Indique si un livre correspondant a été trouvé dans Google Books.",
        json_schema_extra={"example": True},
    )
    google_books_info: dict | None = Field(
        None,
        description="Infos détaillées renvoyées par Google Books.",
        json_schema_extra={
            "example": {
                "title": "Deep Learning",
                "authors": ["Ian Goodfellow", "Yoshua Bengio", "Aaron Courville"],
                "published_date": "2016-11-18",
                "categories": ["Computers"],
                "average_rating": 4.5,
                "ratings_count": 1234,
                "info_link": "https://books.google.com/...",
            }
        },
    )
    google_books_verification: str = Field(
        ...,
        description="Résumé textuel de la vérification Google Books.",
        json_schema_extra={
            "example": "✅ Book found in Google Books! Title: Deep Learning ..."
        },
    )


class DetectResponse(BaseModel):
    num_books: int = Field(..., json_schema_extra={"example": 3})
    original_image: str = Field(
        ...,
        description="Chemin vers l'image originale sauvegardée.",
        json_schema_extra={"example": "/debug_crops/original.jpg"},
    )
    annotated_image: str = Field(
        ...,
        description="Image annotée avec les bounding boxes YOLO.",
        json_schema_extra={"example": "/debug_crops/debug_image.jpg"},
    )


class DetectAndOcrResponse(BaseModel):
    num_books: int = Field(..., json_schema_extra={"example": 3})
    books: List[BookOCR]
    annotated_image: str | None = Field(
        ...,
        description="Image annotée avec les boîtes de détection par livre.",
        json_schema_extra={"example": "/debug_crops/all_books_detected.jpg"},
    )
    original_image: str | None = Field(
        ...,
        description="Copie de l'image originale utilisée pour la détection.",
        json_schema_extra={"example": "/debug_crops/original.jpg"},
    )


class DetectOcrAgentResponse(BaseModel):
    num_books: int = Field(..., json_schema_extra={"example": 3})
    books: List[BookWithAgent]
    annotated_image: str | None = Field(
        ...,
        description="Image annotée avec les boîtes de détection et titres résolus.",
        json_schema_extra={"example": "/debug_crops/all_books_detected.jpg"},
    )
    original_image: str | None = Field(
        ...,
        description="Copie de l'image originale utilisée pour la détection.",
        json_schema_extra={"example": "/debug_crops/original.jpg"},
    )


class ScanAndEnrichResponse(DetectOcrAgentResponse):
    biblio_id: int = Field(
        ...,
        description="Identifiant de la bibliothèque / étagère.",
        json_schema_extra={"example": 1},
    )
    position_ligne: int = Field(
        ...,
        description="Indice de ligne de l'étagère (1 = rangée du haut).",
        json_schema_extra={"example": 1},
    )
    position_colonne: int = Field(
        ...,
        description="Indice de colonne du premier livre scanné.",
        json_schema_extra={"example": 1},
    )


# =========================================================
#  ROUTES API
# =========================================================
@app.post(
    "/upload",
    response_model=UploadResponse,
    tags=["Upload"],
    summary="Uploader une image",
    description="Téléverse une image unique qui sera utilisée par les endpoints de détection/OCR.",
)
async def upload_image(file: UploadFile = File(...)):
    return await upload_controller.upload_image(file)


@app.post(
    "/detect",
    response_model=DetectResponse,
    tags=["Détection"],
    summary="Détecter les livres (YOLO seulement)",
    description=(
        "Utilise le dernier fichier uploadé pour détecter les livres avec YOLO "
        "et renvoie une image annotée ainsi que le nombre de livres détectés."
    ),
)
async def detect(
    conf: float = Query(
        0.6, ge=0.0, le=1.0, description="Seuil de confiance YOLO (0-1)."
    ),
    iou: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil IOU pour la suppression de non-maxima (0-1).",
    ),
):
    return await detection_controller.detect(conf=conf, iou=iou)


@app.post(
    "/detect_and_ocr",
    response_model=DetectAndOcrResponse,
    tags=["OCR"],
    summary="Détecter les livres et lancer l'OCR",
    description=(
        "Détecte les livres sur l'image puis applique l'OCR sur chaque livre "
        "pour extraire le texte et les régions de texte détectées."
    ),
)
async def detect_and_ocr(
    conf: float = Query(
        0.6, ge=0.0, le=1.0, description="Seuil de confiance YOLO (0-1)."
    ),
    iou: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil IOU pour la suppression de non-maxima (0-1).",
    ),
):
    return await detection_controller.detect_and_ocr(conf=conf, iou=iou)


@app.post(
    "/detect_and_ocr_and_agent",
    response_model=DetectOcrAgentResponse,
    tags=["Agents"],
    summary="Détecter les livres, lancer l'OCR et utiliser les agents LLM",
    description=(
        "Pipeline complet : détection des livres, OCR par livre, puis appel d'agents "
        "LLM pour proposer un titre final et un raisonnement pour chaque livre."
    ),
)
async def detect_and_ocr_and_agent(
    conf: float = Query(
        0.6, ge=0.0, le=1.0, description="Seuil de confiance YOLO (0-1)."
    ),
    iou: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil IOU pour la suppression de non-maxima (0-1).",
    ),
):
    return await detection_controller.detect_and_ocr_and_agent(conf=conf, iou=iou)


# =========================================================
#  ENDPOINT MOBILE : SCAN + ENRICHISSEMENT BDD
# =========================================================
@app.post(
    "/scan_and_enrich",
    response_model=ScanAndEnrichResponse,
    tags=["Biblio"],
    summary="Scanner une étagère et enrichir la base de données",
    description=(
        "Upload d'une image + pipeline complet (détection, OCR, agents) puis insertion "
        "en base de données des livres détectés avec leur position (biblio_id, ligne, colonne)."
    ),
)
async def scan_and_enrich(
    file: UploadFile = File(...),
    biblio_id: int = Form(..., description="Identifiant de la bibliothèque / étagère."),
    position_ligne: int = Form(
        ..., description="Numéro de ligne de l'étagère (1 = rangée du haut)."
    ),
    position_colonne: int = Form(
        ..., description="Colonne du premier livre scanné."
    ),
    conf: float = Query(
        0.6, ge=0.0, le=1.0, description="Seuil de confiance YOLO (0-1)."
    ),
    iou: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil IOU pour la suppression de non-maxima (0-1).",
    ),
):
    """
    Pour ton appli mobile :
      - envoie un POST multipart/form-data sur /scan_and_enrich
      - champs :
          * file            -> l'image
          * biblio_id       -> int
          * position_ligne  -> int
          * position_colonne-> int
    """
    # 1) Upload de l'image
    await upload_controller.upload_image(file)

    # 2) Pipeline complet via le controller existant
    result: dict = await detection_controller.detect_and_ocr_and_agent(
        conf=conf, iou=iou
    )

    num_books = result.get("num_books", 0)
    books = result.get("books", [])

    # 3) Insertion BDD
    for idx, book in enumerate(books):
        gb_info = book.get("google_books_info") or {}
        image_links = gb_info.get("image_links") or {}

        titre = (
            gb_info.get("title")
            or book.get("resolved_title")
            or book.get("text")
            or f"Livre {idx+1}"
        )
        auteurs = gb_info.get("authors") or []
        date_pub = gb_info.get("published_date")
        cover = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        isbn = gb_info.get("isbn")  # optionnel (si tu l'ajoutes dans l’agent)

        golden_record = {
            "titre": titre,
            "auteur": ", ".join(auteurs) or "Inconnu",
            "date_pub": date_pub,
            "cover": cover,
            "isbn": isbn,
        }

        col = position_colonne + idx  # colonne de départ + index du livre
        insert_book(
            golden_record=golden_record,
            biblio_id=biblio_id,
            ligne=position_ligne,
            col=col,
        )

    return ScanAndEnrichResponse(
        num_books=num_books,
        books=books,
        annotated_image=result.get("annotated_image"),
        original_image=result.get("original_image"),
        biblio_id=biblio_id,
        position_ligne=position_ligne,
        position_colonne=position_colonne,
    )


# =========================================================
#  DEBUG : servir les crops
# =========================================================
@app.get(
    "/debug_crops/{filename}",
    tags=["Debug"],
    summary="Servir une image de debug (crop)",
)
async def serve_crop(filename: str):
    return await detection_controller.serve_crop(filename)


# =========================================================
#  RUN (dev)
# =========================================================
if __name__ == "__main__":
    print(" Serveur sur http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
