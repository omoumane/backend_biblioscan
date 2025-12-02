"""BiblioScan FastAPI server - Main application entry point"""
from typing import List

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi import File, UploadFile
from pydantic import BaseModel, Field
from pydantic import ConfigDict
import uvicorn

# Import controllers
from controllers import upload_controller, detection_controller

# =========================================================
#  APP CONFIGURATION
# =========================================================
app = FastAPI(
    title="BiblioScan Détection Serveur",
    version="1.0",
    description=(
        "API FastAPI pour l'upload d'images de bibliothèques, la détection de livres "
        "avec YOLO et l'extraction de texte via OCR (et agents LLM pour la résolution de titres)."
    ),
    contact={
        "name": "BiblioScan",
    },
    license_info={
        "name": "Propriétaire (usage interne)",
    },
    openapi_tags=[
        {
            "name": "Upload",
            "description": "Endpoints pour téléverser les images à analyser.",
        },
        {
            "name": "Détection",
            "description": "Endpoints pour détecter les livres sur l'image et obtenir les images annotées.",
        },
        {
            "name": "OCR",
            "description": "Endpoints pour lancer l'OCR sur chaque livre détecté.",
        },
        {
            "name": "Agents",
            "description": "Endpoints pour utiliser des agents LLM afin de résoudre les titres des livres.",
        },
        {
            "name": "Debug",
            "description": "Endpoints internes pour servir les images de debug.",
        },
    ],
    docs_url="/docs",   # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
#  SCHEMA MODELS (for Swagger / OpenAPI)
# =========================================================
class UploadResponse(BaseModel):
    message: str = Field(
        ...,
        description="Message de confirmation après upload.",
        json_schema_extra={"example": " Image uploadée avec succès"},
    )
    path: str = Field(
        ...,
        description="Chemin du fichier image stocké côté serveur.",
        json_schema_extra={"example": "uploaded.jpg"},
    )


class TextDetection(BaseModel):
    text: str = Field(
        ...,
        json_schema_extra={"example": "Deep Learning"},
    )
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
    book_id: int = Field(
        ...,
        json_schema_extra={"example": 0},
    )
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
        description="Label qualitatif basé sur la confiance (excellent / good / fair / poor).",
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

    model_config = ConfigDict(
        validate_by_name=True,
    )


class BookWithAgent(BookOCR):
    resolved_title: str = Field(
        ...,
        description="Titre final résolu par l'agent.",
        json_schema_extra={
            "example": "Deep Learning with Python, 2nd Edition",
        },
    )
    agent_confidence: float = Field(
        ...,
        description="Confiance de l'agent en pourcentage (0-100).",
        json_schema_extra={"example": 95.0},
    )
    agent_reasoning: str = Field(
        ...,
        description="Raisonnement textuel de l'agent pour justifier le titre.",
        json_schema_extra={
            "example": "L'OCR contient 'Deep Learning' et 'Python', croisé avec Google Books.",
        },
    )
    google_books_found: bool = Field(
        ...,
        description="Indique si un livre correspondant a été trouvé dans Google Books.",
        json_schema_extra={"example": True},
    )
    google_books_info: dict | None = Field(
        None,
        description="Informations détaillées renvoyées par l'API Google Books pour le meilleur match.",
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
        description="Résumé textuel de la vérification Google Books (trouvé / pas trouvé, détails).",
        json_schema_extra={
            "example": "✅ Book found in Google Books! Title: Deep Learning ...",
        },
    )


class DetectResponse(BaseModel):
    num_books: int = Field(
        ...,
        json_schema_extra={"example": 3},
    )
    original_image: str = Field(
        ...,
        description="Chemin vers l'image originale sauvegardée.",
        json_schema_extra={"example": "/debug_crops/original.jpg"},
    )
    annotated_image: str = Field(
        ...,
        description="Image originale annotée avec les bounding boxes YOLO.",
        json_schema_extra={"example": "/debug_crops/debug_image.jpg"},
    )


class DetectAndOcrResponse(BaseModel):
    num_books: int = Field(
        ...,
        json_schema_extra={"example": 3},
    )
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
    num_books: int = Field(
        ...,
        json_schema_extra={"example": 3},
    )
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


# =========================================================
#  ROUTES
# =========================================================
@app.post(
    "/upload",
    response_model=UploadResponse,
    tags=["Upload"],
    summary="Uploader une image",
    description="Téléverse une image unique qui sera utilisée par les endpoints de détection/OCR.",
)
async def upload_image(file: UploadFile = File(...)):
    """Upload image endpoint."""
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
        0.6,
        ge=0.0,
        le=1.0,
        description="Seuil de confiance YOLO (0-1).",
    ),
    iou: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil IOU pour la suppression de non-maxima (0-1).",
    ),
):
    """Detect books endpoint."""
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
        0.6,
        ge=0.0,
        le=1.0,
        description="Seuil de confiance YOLO (0-1).",
    ),
    iou: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil IOU pour la suppression de non-maxima (0-1).",
    ),
):
    """Detect books and run OCR endpoint."""
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
        0.6,
        ge=0.0,
        le=1.0,
        description="Seuil de confiance YOLO (0-1).",
    ),
    iou: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Seuil IOU pour la suppression de non-maxima (0-1).",
    ),
):
    """Detect books, run OCR, and resolve titles using agents."""
    return await detection_controller.detect_and_ocr_and_agent(conf=conf, iou=iou)


@app.get(
    "/debug_crops/{filename}",
    tags=["Debug"],
    summary="Servir une image de debug (crop)",
)
async def serve_crop(filename: str):
    """Serve crop images for debugging."""
    return await detection_controller.serve_crop(filename)


@app.get(
    "/",
    response_class=HTMLResponse,
    tags=["Debug"],
    summary="Interface web de démonstration",
    description=(
        "Page HTML simple pour téléverser une image, lancer la détection/OCR "
        "et visualiser les résultats."
    ),
)
async def index(request: Request):
    """Web interface"""
    html = """
    <html>
    <head>
        <title>BiblioScan - Détection & OCR</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; text-align:center; background:#f5f6fa; color:#222; padding:20px; }
            h2 { color:#006666; }
            button { background:#008080; color:white; padding:10px 20px; border:none; border-radius:8px; cursor:pointer; margin:5px; font-size:14px; }
            button:hover { background:#009999; }
            button:disabled { background:#ccc; cursor:not-allowed; }
            .images { display:flex; justify-content:center; gap:25px; margin-top:25px; flex-wrap:wrap; }
            .image-container { text-align:center; }
            img { border-radius:10px; box-shadow:0 3px 8px rgba(0,0,0,0.2); max-width:400px; }
            #status { font-weight:bold; color:#008080; margin:15px 0; }
            .ocr-results { background:white; border-radius:10px; padding:20px; margin:20px auto; max-width:800px; box-shadow:0 3px 8px rgba(0,0,0,0.1); }
            .ocr-text { font-size:18px; margin:15px 0; padding:15px; background:#e8f8f5; border-radius:8px; font-style:italic; }
            .confidence { display:inline-block; padding:5px 15px; border-radius:20px; font-weight:bold; margin:10px 5px; }
            .excellent { background:#2ecc71; color:white; }
            .good { background:#3498db; color:white; }
            .fair { background:#f39c12; color:white; }
            .poor { background:#e74c3c; color:white; }
            .detections { text-align:left; margin-top:15px; }
            .detection-item { background:#f8f9fa; padding:8px; margin:5px 0; border-radius:5px; border-left:3px solid #008080; }
            .button-group { margin:15px 0; }
        </style>
    </head>
    <body>
        <h2>📚 BiblioScan - Détection & OCR de livres</h2>
        <form id="uploadForm">
            <input type="file" id="fileInput" accept="image/*" required>
            <button type="submit">⬆️ Uploader l'image</button>
        </form>
        
        <div class="button-group">
            <button id="detectBtn" onclick="detectBooks()" disabled>🔍 Détecter les livres</button>
            <button id="detectOcrBtn" onclick="detectAndOcrBooks()" disabled>🔍📝 Détecter + OCR par livre</button>
            <button id="detectOcrAgentBtn" onclick="detectAndOcrAndAgentBooks()" disabled>🤖🔍📝 Détecter + OCR + Agent</button>
        </div>
        
        <p id="status"></p>
        <div id="results"></div>
        <div id="ocrResults"></div>

        <script>
        const status = document.getElementById("status");
        const detectBtn = document.getElementById("detectBtn");
        const detectOcrBtn = document.getElementById("detectOcrBtn");
        const detectOcrAgentBtn = document.getElementById("detectOcrAgentBtn");
        let imageUploaded = false;

        document.getElementById("uploadForm").onsubmit = async (e) => {
            e.preventDefault();
            let file = document.getElementById("fileInput").files[0];
            let form = new FormData();
            form.append("file", file);
            status.innerText = "⏳ Upload en cours...";
            await fetch("/upload", {method:"POST", body:form});
            status.innerText = "✅ Image uploadée avec succès !";
            imageUploaded = true;
            detectBtn.disabled = false;
            detectOcrBtn.disabled = false;
            detectOcrAgentBtn.disabled = false;
            document.getElementById("results").innerHTML = "";
            document.getElementById("ocrResults").innerHTML = "";
        };

        async function detectBooks() {
            if (!imageUploaded) return;
            status.innerText = "🔍 Détection en cours...";
            detectBtn.disabled = true;
            const res = await fetch("/detect", {method:"POST"});
            const data = await res.json();
            status.innerText = "✅ Détection terminée";
            detectBtn.disabled = false;
            document.getElementById("results").innerHTML = `
                <div class='images'>
                    <div class='image-container'>
                        <h3>Image originale</h3>
                        <img src="${data.original_image}?t=${Date.now()}" width="400">
                    </div>
                    <div class='image-container'>
                        <h3>Livres détectés</h3>
                        <img src="${data.annotated_image}?t=${Date.now()}" width="400">
                    </div>
                </div>
                <h3>📚 Nombre de livres détectés : ${data.num_books}</h3>`;
        }

        async function detectAndOcrBooks() {
            if (!imageUploaded) return;
            status.innerText = "🔍📝 Détection et OCR par livre en cours...";
            detectOcrBtn.disabled = true;
            const res = await fetch("/detect_and_ocr", {method:"POST"});
            const data = await res.json();
            status.innerText = "✅ Détection et OCR terminés";
            detectOcrBtn.disabled = false;
            
            if (data.num_books === 0) {
                document.getElementById("results").innerHTML = "<h3>❌ Aucun livre détecté</h3>";
                return;
            }
            
            let booksHtml = "";
            data.books.forEach(book => {
                let confidenceClass = book.ocr_quality.toLowerCase();
                booksHtml += `
                    <div class="ocr-results" style="margin:20px auto;">
                        <h3>📕 Livre ${book.book_id + 1}</h3>
                        <div style="display:flex; gap:15px; justify-content:center; flex-wrap:wrap; margin:15px 0;">
                            <div>
                                <h4>Crop original</h4>
                                <img src="${book.crop_image}?t=${Date.now()}" style="max-width:250px;">
                            </div>
                            <div>
                                <h4>Détections OCR</h4>
                                <img src="${book.crop_image_annotated}?t=${Date.now()}" style="max-width:250px;">
                            </div>
                        </div>
                        
                        <div class="ocr-text">
                            <strong>Texte extrait :</strong><br>
                            "${book.text || 'Aucun texte détecté'}"
                        </div>
                        
                        <div>
                            <span class="confidence ${confidenceClass}">
                                OCR Confiance : ${book.ocr_confidence}% (${book.ocr_quality})
                            </span>
                            <span style="margin-left:10px; color:#666;">
                                Détection YOLO : ${(book.detection_confidence * 100).toFixed(1)}%
                            </span>
                        </div>
                        
                        ${book.text_detections.length > 0 ? `
                            <div class="detections">
                                <h4>Détails (${book.num_text_detections} détections) :</h4>
                                ${book.text_detections.map((d, i) => `
                                    <div class="detection-item">
                                        <strong>${i+1}.</strong> "${d.text}" 
                                        <span style="float:right; color:#008080;">${d.confidence}%</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            document.getElementById("results").innerHTML = `
                <div style="margin:20px 0;">
                    <h3>📚 ${data.num_books} livre(s) détecté(s) et analysé(s)</h3>
                    <div style="margin:15px 0;">
                        <img src="${data.annotated_image}?t=${Date.now()}" width="600" style="border-radius:10px;">
                    </div>
                </div>
            `;
            
            document.getElementById("ocrResults").innerHTML = booksHtml;
        }

        async function detectAndOcrAndAgentBooks() {
            if (!imageUploaded) return;
            status.innerText = "🤖🔍📝 Détection, OCR et résolution par agent en cours...";
            detectOcrAgentBtn.disabled = true;
            const res = await fetch("/detect_and_ocr_and_agent", {method:"POST"});
            const data = await res.json();
            status.innerText = "✅ Détection, OCR et résolution terminés";
            detectOcrAgentBtn.disabled = false;
            
            if (data.num_books === 0) {
                document.getElementById("results").innerHTML = "<h3>❌ Aucun livre détecté</h3>";
                return;
            }
            
            let booksHtml = "";
            data.books.forEach(book => {
                let confidenceClass = book.ocr_quality.toLowerCase();
                let agentConfidenceClass = book.agent_confidence >= 70 ? "excellent" : 
                                         book.agent_confidence >= 50 ? "good" : 
                                         book.agent_confidence >= 30 ? "fair" : "poor";
                booksHtml += `
                    <div class="ocr-results" style="margin:20px auto;">
                        <h3>📕 Livre ${book.book_id + 1}</h3>
                        <div style="display:flex; gap:15px; justify-content:center; flex-wrap:wrap; margin:15px 0;">
                            <div>
                                <h4>Crop original</h4>
                                <img src="${book.crop_image}?t=${Date.now()}" style="max-width:250px;">
                            </div>
                            <div>
                                <h4>Détections OCR</h4>
                                <img src="${book.crop_image_annotated}?t=${Date.now()}" style="max-width:250px;">
                            </div>
                        </div>
                        
                        <div class="ocr-text">
                            <strong>Texte OCR extrait :</strong><br>
                            "${book.text || 'Aucun texte détecté'}"
                        </div>
                        
                        ${book.resolved_title ? `
                        <div class="ocr-text" style="background:#fff3cd; border:2px solid #ffc107;">
                            <strong>🤖 Titre résolu par l'agent :</strong><br>
                            "<strong style="font-size:20px; color:#006666;">${book.resolved_title}</strong>"
                        </div>
                        ` : ''}
                        
                        ${book.google_books_found && book.google_books_info ? `
                        <div class="ocr-text" style="background:#d4edda; border:2px solid #28a745;">
                            <strong>📚 Vérification Google Books :</strong><br>
                            <div style="margin-top:10px;">
                                ${book.google_books_info.authors && book.google_books_info.authors.length > 0 ? `
                                    <div><strong>Auteur(s):</strong> ${book.google_books_info.authors.join(', ')}</div>
                                ` : ''}
                                ${book.google_books_info.published_date ? `
                                    <div><strong>Publié:</strong> ${book.google_books_info.published_date}</div>
                                ` : ''}
                                ${book.google_books_info.categories && book.google_books_info.categories.length > 0 ? `
                                    <div><strong>Catégories:</strong> ${book.google_books_info.categories.slice(0, 3).join(', ')}</div>
                                ` : ''}
                                ${book.google_books_info.average_rating > 0 ? `
                                    <div><strong>Note:</strong> ${book.google_books_info.average_rating}/5 (${book.google_books_info.ratings_count} avis)</div>
                                ` : ''}
                                ${book.google_books_info.info_link ? `
                                    <div style="margin-top:8px;">
                                        <a href="${book.google_books_info.info_link}" target="_blank" style="color:#006666; text-decoration:underline;">
                                            🔗 Voir sur Google Books
                                        </a>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                        ` : book.google_books_verification ? `
                        <div class="ocr-text" style="background:#fff3cd; border:2px solid #ffc107;">
                            <strong>📚 Vérification Google Books :</strong><br>
                            <div style="margin-top:10px; white-space:pre-line;">${book.google_books_verification}</div>
                        </div>
                        ` : ''}
                        
                        <div>
                            <span class="confidence ${confidenceClass}">
                                OCR Confiance : ${book.ocr_confidence}% (${book.ocr_quality})
                            </span>
                            <span style="margin-left:10px; color:#666;">
                                Détection YOLO : ${(book.detection_confidence * 100).toFixed(1)}%
                            </span>
                            ${book.resolved_title ? `
                            <span class="confidence ${agentConfidenceClass}" style="margin-left:10px;">
                                Agent Confiance : ${book.agent_confidence}%
                            </span>
                            ` : ''}
                            ${book.google_books_found ? `
                            <span class="confidence excellent" style="margin-left:10px;">
                                ✅ Google Books
                            </span>
                            ` : ''}
                        </div>
                        
                        ${book.agent_reasoning ? `
                            <div style="margin-top:10px; padding:10px; background:#f8f9fa; border-radius:5px; font-size:14px; color:#666;">
                                <strong>💭 Raisonnement de l'agent :</strong><br>
                                ${book.agent_reasoning}
                            </div>
                        ` : ''}
                        
                        ${book.text_detections.length > 0 ? `
                            <div class="detections">
                                <h4>Détails (${book.num_text_detections} détections) :</h4>
                                ${book.text_detections.map((d, i) => `
                                    <div class="detection-item">
                                        <strong>${i+1}.</strong> "${d.text}" 
                                        <span style="float:right; color:#008080;">${d.confidence}%</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            document.getElementById("results").innerHTML = `
                <div style="margin:20px 0;">
                    <h3>📚 ${data.num_books} livre(s) détecté(s), analysé(s) et résolu(s)</h3>
                    <div style="margin:15px 0;">
                        <img src="${data.annotated_image}?t=${Date.now()}" width="600" style="border-radius:10px;">
                    </div>
                </div>
            `;
            
            document.getElementById("ocrResults").innerHTML = booksHtml;
        }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

# =========================================================
#  RUN
# =========================================================
if __name__ == "__main__":
    print(" Serveur sur http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
