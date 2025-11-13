import os
import re
import cv2
import json
import numpy as np
import torch
import easyocr
import requests
from ultralytics import YOLO
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from dotenv import load_dotenv
from openai import OpenAI

# =========================================================
# 🌍 CONFIGURATION GÉNÉRALE
# =========================================================
app = FastAPI(title="📚 BiblioScan - YOLO + EasyOCR + Groq + GoogleBooks", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise SystemExit("❌ Clé GROQ_API_KEY manquante dans .env")

# Client Groq (compatible OpenAI)
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"
client = OpenAI()

# =========================================================
# ⚙ CHARGEMENT DES MODÈLES
# =========================================================
MODEL_PATH = "./models/bookshelf_best.pt"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"➡ Device : {DEVICE}")

model = YOLO(MODEL_PATH)
model.to(DEVICE)
print(f"✅ YOLO chargé depuis {MODEL_PATH}")

print("🔠 Initialisation EasyOCR...")
reader = easyocr.Reader(['fr', 'en'], gpu=(DEVICE == "cuda"), verbose=False)
print(f"✅ EasyOCR prêt (GPU: {DEVICE == 'cuda'})")

# =========================================================
#  CHEMINS
# =========================================================
UPLOAD_PATH = "uploaded.jpg"
os.makedirs("debug_crops", exist_ok=True)
ORIGINAL_PATH = "debug_crops/original.jpg"

# =========================================================
#  OCR UTILS
# =========================================================
def preprocess_image(img):
    # Gris + equalize hist -> OCR robuste pour tranches
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.equalizeHist(gray)
    return enhanced

def clean_text(results):
    if not results:
        return ""
    texts = [item[1] for item in results]
    text = ' '.join(texts)
    text = ' '.join(text.split())
    # Pas de .title() agressif (garde les majuscules propres de noms)
    return text

def calculate_confidence(results):
    if not results:
        return 0.0
    confidences = [float(item[2]) for item in results]
    return sum(confidences) / len(confidences)

def get_confidence_label(c):
    if c >= 0.9: return "Excellent"
    if c >= 0.7: return "Good"
    if c >= 0.5: return "Fair"
    return "Poor"

# =========================================================
# 🤖 LLM (Groq) — Clean mode + extraction stricte JSON
# =========================================================
def correct_with_groq(text):
    """Correction OCR minimaliste (accents/lettres), pas de traduction."""
    if not text.strip():
        return ""
    try:
        prompt = f"""
Texte OCR détecté :
{text}

Tâches :
1) Corrige uniquement les erreurs d'OCR évidentes (lettres/accents).
2) Si tu reconnais un auteur classique (Balzac, Zola, Gide, Apollinaire, Shakespeare,
   Radiguet, Fante, Hugo, Proust, Molière, Dhôtel), corrige le nom.
3) Ne traduis rien et ne rajoute pas d'explication.
Réponds UNIQUEMENT par le texte corrigé.
"""
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=60
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as e:
        print("⚠ Erreur Groq (correction):", e)
        return text

def extract_metadata_with_groq(text):
    """Retour JSON strict: {'titre':..., 'auteur':..., 'collection':...}"""
    try:
        prompt = f"""
Analyse ce texte corrigé (titre/auteur/collection possibles) :
{text}

Règles :
- Réponds UNIQUEMENT en JSON valide.
- Si inconnu -> null.

Exemple JSON :
{{"titre":"La Peau de Chagrin","auteur":"Honoré de Balzac","collection":"Classiques & Cie Lycée"}}
"""
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=120
        )
        content = (r.choices[0].message.content or "").strip()
        try:
            data = json.loads(content)
            # Normalise clés manquantes
            return {
                "titre": data.get("titre"),
                "auteur": data.get("auteur"),
                "collection": data.get("collection")
            }
        except json.JSONDecodeError:
            return {"titre": text, "auteur": None, "collection": None}
    except Exception as e:
        print("⚠ Erreur Groq (metadata):", e)
        return {"titre": text, "auteur": None, "collection": None}

def validate_match_with_groq(ocr_text, google_title, google_author):
    """Valide OCR vs GoogleBooks: 'Oui' ou 'Non' uniquement."""
    try:
        prompt = f"""
OCR : {ocr_text}
Google Books : {google_title} – {google_author}
Réponds uniquement par "Oui" ou "Non".
"""
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.1,
            max_tokens=5
        )
        out = (r.choices[0].message.content or "").strip()
        return "Oui" if out.lower().startswith("o") else ("Non" if out.lower().startswith("n") else "Inconnu")
    except Exception as e:
        print("⚠ Erreur Groq (validation):", e)
        return "Inconnu"

# =========================================================
# 📚 GOOGLE BOOKS
# =========================================================
def _find_isbn(ids):
    if not ids:
        return None
    isbn = None
    for i in ids:
        typ = i.get("type")
        ident = i.get("identifier")
        if typ == "ISBN_13" and ident:
            return ident
        if typ == "ISBN_10" and ident:
            isbn = ident
    return isbn

def search_google_books(query):
    if not GOOGLE_API_KEY or not query.strip():
        return {}
    try:
        params = {
            'q': query,
            'maxResults': 1,
            'key': GOOGLE_API_KEY,
            'langRestrict': 'fr'
        }
        r = requests.get("https://www.googleapis.com/books/v1/volumes", params=params, timeout=6)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"⚠ Erreur Google Books : {e}")
        return {}

    if "items" not in data or not data["items"]:
        return {}
    info = data["items"][0].get("volumeInfo", {})
    return {
        "titre": info.get("title", query),
        "auteurs": info.get("authors", []),
        "date_pub": info.get("publishedDate"),
        "isbn": _find_isbn(info.get("industryIdentifiers")),
        "cover": info.get("imageLinks", {}).get("thumbnail")
    }

# =========================================================
# 🧱 HOOKS ETL (Lotfi) — Désactivés par défaut
# =========================================================
ENABLE_DB = False  # 🔴 laisser False. Othmane mettra True + ses identifiants.
db_config = {
    "host": "127.0.0.1",
    "user": "root",        # <-- à remplir
    "password": "password",# <-- à remplir
    "database": "bibliodb" # <-- à remplir
}

def create_db_connection():
    """Retourne None si DB désactivée"""
    if not ENABLE_DB:
        print("ℹ DB désactivée (ENABLE_DB=False). Skip connexion.")
        return None
    try:
        import mysql.connector
        conn = mysql.connector.connect(**db_config)
        return conn
    except Exception as e:
        print(f"❌ Erreur connexion MySQL : {e}")
        return None

def load_to_database(golden_record: dict, biblio_id: int, ligne: int, col: int):
    """Insère/MàJ livre (doublons ISBN->titre). Ne fait rien si DB OFF."""
    if not ENABLE_DB:
        print("ℹ DB désactivée — LOAD ignoré.")
        return
    if not golden_record:
        print("❌ Golden Record vide — LOAD annulé.")
        return

    conn = create_db_connection()
    if not conn:
        print("❌ Connexion DB impossible.")
        return
    try:
        cursor = conn.cursor(dictionary=True)
        book_id = -1

        if golden_record.get("isbn"):
            cursor.execute("SELECT livre_id FROM livres WHERE isbn=%s", (golden_record["isbn"],))
            r = cursor.fetchone()
            if r:
                book_id = r["livre_id"]

        if book_id == -1:
            cursor.execute(
                "SELECT livre_id FROM livres WHERE titre=%s AND biblio_id=%s",
                (golden_record["titre"], biblio_id)
            )
            r = cursor.fetchone()
            if r:
                book_id = r["livre_id"]

        if book_id != -1:
            cursor.execute(
                "UPDATE livres SET biblio_id=%s, position_ligne=%s, position_colonne=%s WHERE livre_id=%s",
                (biblio_id, ligne, col, book_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO livres
                  (biblio_id, titre, auteur, date_pub, position_ligne, position_colonne, couverture_url, isbn)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    biblio_id,
                    golden_record.get("titre"),
                    golden_record.get("auteur"),
                    golden_record.get("date_pub"),
                    ligne, col,
                    golden_record.get("cover"),
                    golden_record.get("isbn"),
                )
            )
        conn.commit()
    except Exception as e:
        print(f"❌ Erreur LOAD DB : {e}")
        try:
            conn.rollback()
        except:
            pass
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

# =========================================================
# 🔁 PIPELINE PRINCIPAL
# =========================================================
@app.post("/scan_and_enrich")
async def scan_and_enrich(
    file: UploadFile = File(...),
    biblio_id: int = Form(...),
    position_ligne: int = Form(...),
    position_colonne: int = Form(...)
):
    """
    Pipeline complet.
    Entrées :
      - image (file)
      - biblio_id (int)
      - position_ligne (int)
      - position_colonne (int)

    Si ENABLE_DB=True, on tente le LOAD avec (biblio_id, position_ligne, position_colonne + idx).
    """
    content = await file.read()
    with open(UPLOAD_PATH, "wb") as f:
        f.write(content)

    img = cv2.imread(UPLOAD_PATH)
    if img is None:
        return JSONResponse({"message": "❌ Image invalide."}, status_code=400)

    cv2.imwrite(ORIGINAL_PATH, img)

    print("📸 Image size:", img.shape)
    results = model.predict(
        UPLOAD_PATH,
        conf=0.3,
        iou=0.5,
        imgsz=640,
        device=DEVICE,
        verbose=True
    )[0]

    print("📦 YOLO - nombre de boxes:", len(results.boxes))

    if len(results.boxes) == 0:
        return JSONResponse({
            "message": "❌ Aucun livre détecté (YOLO=0 boxes dans FastAPI).",
            "books_detected": 0
        })

    # 3) Prépare tri par orientation
    detections = list(zip(
        results.boxes.xyxy.cpu().numpy(),
        results.boxes.conf.cpu().numpy(),
        results.boxes.cls.cpu().numpy()
    ))
    x_positions = [b[0][0] for b in detections]
    y_positions = [b[0][1] for b in detections]
    spread_x = max(x_positions) - min(x_positions)
    spread_y = max(y_positions) - min(y_positions)

    if spread_y > spread_x:
        print("📚 Disposition détectée : verticale (tri haut→bas)")
        detections.sort(key=lambda x: x[0][1])
    else:
        print("📚 Disposition détectée : horizontale (tri gauche→droite)")
        detections.sort(key=lambda x: x[0][0])

    annotated = img.copy()
    out_data = []

    for idx, (box, score, cls) in enumerate(detections):
        x1, y1, x2, y2 = map(int, box)
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        crop_path = f"debug_crops/book_{idx}.jpg"
        crop_annot_path = f"debug_crops/book_{idx}_ocr.jpg"
        cv2.imwrite(crop_path, crop)

        # 4) OCR
        oimg = preprocess_image(crop)
        ocr_results = reader.readtext(oimg)
        cleaned = clean_text(ocr_results)
        avg_conf = calculate_confidence(ocr_results)
        qual = get_confidence_label(avg_conf)

        # Annoter OCR sur le crop
        annotated_crop = crop.copy()
        for bbox, txt, conf in ocr_results:
            pts = np.array(bbox).astype(np.int32)
            cv2.polylines(annotated_crop, [pts], True, (0, 255, 0), 2)
        cv2.imwrite(crop_annot_path, annotated_crop)

        # 5) LLM correction + metadata + GoogleBooks + validation
        corrected = correct_with_groq(cleaned)
        meta = extract_metadata_with_groq(corrected)
        q = f"{meta.get('titre') or corrected} {meta.get('auteur') or ''}".strip()
        g = search_google_books(q) if q else {}
        validation = validate_match_with_groq(
            corrected,
            g.get("titre", ""),
            ", ".join(g.get("auteurs", []))
        ) if g else "Inconnu"

        # Dessin sur l'image globale
        label = (meta.get("titre") or corrected or f"Book {idx}")[:26]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(
            annotated,
            label,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # 6) LOAD DB (si activé)
        golden_record = {
            "titre": g.get("titre") or (meta.get("titre") or corrected),
            "auteur": ", ".join(g.get("auteurs", [])) or (meta.get("auteur") or "Inconnu"),
            "date_pub": g.get("date_pub"),
            "cover": g.get("cover"),
            "isbn": g.get("isbn")
        }

        # Position : on fixe la ligne, on décale la colonne par idx
        load_to_database(
            golden_record=golden_record,
            biblio_id=biblio_id,
            ligne=position_ligne,
            col=position_colonne + idx
        )

        out_data.append({
            "google_books": g,
            # "crop_image": f"/debug_crops/book_{idx}.jpg",
            # "crop_image_annotated": f"/debug_crops/book_{idx}_ocr.jpg"
        })

    annotated_path = "debug_crops/all_books_detected.jpg"
    cv2.imwrite(annotated_path, annotated)

    return JSONResponse({
        "message": "✅ Détection + OCR + Correction + Enrichissement terminés.",
        "books_detected": len(out_data),
        "annotated_image": "/debug_crops/all_books_detected.jpg",
        "biblio_id": biblio_id,
        "position_ligne": position_ligne,
        "position_colonne": position_colonne,
        "results": out_data
    })


# =========================================================
# 🌐 SERVE LES IMAGES
# =========================================================
@app.get("/debug_crops/{filename}")
async def serve_crop(filename: str):
    return FileResponse(os.path.join("debug_crops", filename))

# =========================================================
# 🌐 INTERFACE WEB
# =========================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>BiblioScan OCR enrichi</title>
</head>
<body style="font-family:sans-serif;text-align:center;background:#f8f9fa;color:#222;">
    <h2>📚 BiblioScan - YOLO + EasyOCR + Groq + GoogleBooks</h2>

    <form id="uploadForm" enctype="multipart/form-data">
        <div style="margin-bottom:10px;">
            <input type="file" id="fileInput" accept="image/*" required>
        </div>
        <div style="margin-bottom:10px;">
            <input type="number" id="biblioId" placeholder="biblio_id" style="width:180px;">
            <input type="number" id="posLigne" placeholder="position_ligne" style="width:180px;margin-left:8px;">
            <input type="number" id="posCol" placeholder="position_colonne" style="width:180px;margin-left:8px;">
        </div>
        <button type="submit">📤 Uploader & Scanner</button>
    </form>

    <p id="status"></p>
    <div id="results"></div>

    <script>
    // On attend le chargement complet de la page
    window.addEventListener('load', function () {
        console.log("✅ JS chargé");
        var form = document.getElementById('uploadForm');
        var status = document.getElementById('status');
        var resultsDiv = document.getElementById('results');

        form.addEventListener('submit', function (e) {
            e.preventDefault(); // EMPÊCHE le rechargement de page

            var fileInput = document.getElementById('fileInput');
            var biblioInput = document.getElementById('biblioId');
            var posLigneInput = document.getElementById('posLigne');
            var posColInput = document.getElementById('posCol');

            var file = fileInput.files[0];
            var biblio = biblioInput.value || 0;
            var posLigne = posLigneInput.value || 1;
            var posCol = posColInput.value || 1;

            if (!file) {
                status.innerText = "⚠️ Merci de choisir une image.";
                return;
            }

            var formData = new FormData();
            formData.append('file', file);

            status.innerText = "⏳ Analyse en cours...";
            resultsDiv.innerHTML = "";

            var url = '/scan_and_enrich'
                + '?biblio_id=' + encodeURIComponent(biblio)
                + '&position_ligne=' + encodeURIComponent(posLigne)
                + '&position_colonne=' + encodeURIComponent(posCol);

            var xhr = new XMLHttpRequest();
            xhr.open('POST', url, true);

            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    console.log("Réponse reçue, status =", xhr.status);
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            console.log("JSON:", data);
                            status.innerText = data.message || "OK";

                            var html = "";
                            html += "<h3>" + (data.books_detected || 0) + " livre(s) détecté(s)</h3>";

                            if (data.annotated_image) {
                                html += '<img src="' + data.annotated_image + '?t=' + Date.now() + '" width="640" style="border-radius:10px;"><br>';
                            }

                            if (data.results && data.results.length > 0) {
                                for (var i = 0; i < data.results.length; i++) {
                                    var b = data.results[i];
                                    html += "<div style='margin:20px auto;width:85%;background:white;padding:15px;border-radius:10px;text-align:left;box-shadow:0 2px 8px rgba(0,0,0,.06);'>";
                                    html += "<h4>📘 " + ( 
                                        (b.google_books && b.google_books.titre) ||
                                        (b.metadata_extracted && b.metadata_extracted.titre) ||
                                        b.llm_correction ||
                                        "Titre inconnu"
                                    ) + "</h4>";

                                    html += "<p><b>OCR brut :</b> " + (b.ocr_text || "") + "</p>";
                                    html += "<p><b>Correction :</b> " + (b.llm_correction || "") + "</p>";

                                    if (b.metadata_extracted) {
                                        html += "<p><b>Métadonnées (LLM) :</b> " +
                                            (b.metadata_extracted.titre || "-") + " • " +
                                            (b.metadata_extracted.auteur || "-") + " • " +
                                            (b.metadata_extracted.collection || "-") + "</p>";
                                    }

                                    html += "<p><b>Qualité OCR :</b> " + b.ocr_quality + " (" + b.ocr_confidence + "%)</p>";
                                    html += "<p><b>Confiance YOLO :</b> " + b.yolo_confidence + "%</p>";
                                    html += "<p><b>Validation :</b> " + (b.validation_result || "Inconnu") + "</p>";

                                    html += "<div style='display:flex;gap:15px;flex-wrap:wrap;align-items:flex-start;'>";
                                    if (b.crop_image) {
                                        html += "<div><img src='" + b.crop_image + "?t=" + Date.now() + "' width='220'><br><small>Crop original</small></div>";
                                    }
                                    if (b.crop_image_annotated) {
                                        html += "<div><img src='" + b.crop_image_annotated + "?t=" + Date.now() + "' width='220'><br><small>OCR annoté</small></div>";
                                    }
                                    if (b.google_books && b.google_books.cover) {
                                        html += "<div><img src='" + b.google_books.cover + "' width='120'><br><small>Couverture</small></div>";
                                    }
                                    html += "</div>";

                                    if (b.google_books) {
                                        if (b.google_books.auteurs && b.google_books.auteurs.length > 0) {
                                            html += "<p><i>Auteurs : " + b.google_books.auteurs.join(", ") + "</i></p>";
                                        }
                                        if (b.google_books.isbn) {
                                            html += "<p><b>ISBN :</b> " + b.google_books.isbn + "</p>";
                                        }
                                    }

                                    html += "</div>";
                                }
                            }

                            resultsDiv.innerHTML = html;
                        } catch (err) {
                            console.error("Erreur parse JSON:", err);
                            status.innerText = "❌ Erreur de parsing JSON (voir console).";
                        }
                    } else {
                        console.error("Réponse erreur:", xhr.responseText);
                        status.innerText = "❌ Erreur serveur " + xhr.status;
                    }
                }
            };

            xhr.onerror = function () {
                console.error("Erreur XHR");
                status.innerText = "❌ Erreur réseau (XHR).";
            };

            xhr.send(formData);
        });
    });
    </script>
</body>
</html>
"""
    return HTMLResponse(html)

# =========================================================
# 🚀 LANCEMENT
# =========================================================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Serveur sur http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)