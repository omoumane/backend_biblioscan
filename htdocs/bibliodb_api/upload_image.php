<?php
header('Content-Type: application/json; charset=utf-8');

include 'config.php';
include 'verify_token.php';

try {
    // 1) Méthode requise
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        http_response_code(405);
        echo json_encode(["status" => "error", "message" => "Méthode non autorisée. Utilisez POST."]); exit;
    }

    // 2) Champs requis (image & biblio_id). Positions sont désormais optionnelles
    if (!isset($_FILES['image']) || !isset($_POST['biblio_id'])) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Champs requis: image, biblio_id"]); exit;
    }

    $user_id = verifyToken($conn);
    if ($user_id <= 0) {
        http_response_code(401);
        echo json_encode(["status" => "error", "message" => "Token invalide ou expiré"]); exit;
    }

    // 3) Nettoyage/parse
    $biblio_id        = intval($_POST['biblio_id']);
    $position_ligne   = isset($_POST['position_ligne'])   ? intval($_POST['position_ligne'])   : null;
    $position_colonne = isset($_POST['position_colonne']) ? intval($_POST['position_colonne']) : null;

    if ($biblio_id <= 0) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "biblio_id invalide"]); exit;
    }

    if ($position_ligne !== null && $position_ligne < 0) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "position_ligne invalide (>= 0)"]); exit;
    }
    if ($position_colonne !== null && $position_colonne < 0) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "position_colonne invalide (>= 0)"]); exit;
    }

    // Paramètres optionnels YOLO
    $conf = isset($_POST['conf']) ? strval($_POST['conf']) : null;
    $iou  = isset($_POST['iou'])  ? strval($_POST['iou'])  : null;

    // 4) Validation du fichier
    if (!is_uploaded_file($_FILES['image']['tmp_name'])) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Fichier image non reçu"]); exit;
    }

    $tmpName  = $_FILES['image']['tmp_name'];
    $origName = $_FILES['image']['name'] ?? 'upload.bin';
    $size     = $_FILES['image']['size'] ?? 0;

    $maxSizeBytes = 10 * 1024 * 1024; // 10 MB
    if ($size <= 0 || $size > $maxSizeBytes) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Taille de fichier invalide (max 10MB)"]); exit;
    }

    if (!class_exists('finfo')) {
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Extension fileinfo non disponible sur PHP"]); exit;
    }
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mime  = $finfo->file($tmpName);

    $allowed = ['image/jpeg','image/png','image/webp','image/gif'];
    if (!in_array($mime, $allowed, true)) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Type d'image non supporté"]); exit;
    }

    // 5) Requête vers FastAPI
    $fastapiUrl = 'https://fancy-dog-formally.ngrok-free.app/ai/scan_and_enrich';
    $curlFile = new CURLFile($tmpName, $mime, $origName);

    $postFields = [
        'file'      => $curlFile,
        'biblio_id' => (string)$biblio_id,
    ];


    if ($position_ligne !== null)   { $postFields['position_ligne']   = (string)$position_ligne; }
    if ($position_colonne !== null) { $postFields['position_colonne'] = (string)$position_colonne; }
    if ($conf !== null)             { $postFields['conf']             = $conf; }
    if ($iou !== null)              { $postFields['iou']              = $iou; }

    // Transfert de l'Authorization si présent
    $authHeader = '';
    if (function_exists('getallheaders')) {
        $headers = getallheaders();
        if (isset($headers['Authorization']))      { $authHeader = $headers['Authorization']; }
        elseif (isset($headers['authorization'])) { $authHeader = $headers['authorization']; }
    }

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL            => $fastapiUrl,
        CURLOPT_POST           => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POSTFIELDS     => $postFields,
        CURLOPT_HTTPHEADER     => array_filter([
            $authHeader ? "Authorization: $authHeader" : null,
            'Expect:'
        ]),
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT        => 90,
        CURLOPT_FOLLOWLOCATION => false,
    ]);

    $response = curl_exec($ch);
    $curlErr  = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($curlErr) {
        http_response_code(502);
        echo json_encode(["status" => "error", "message" => "Erreur cURL: ".$curlErr]); exit;
    }

    // Si FastAPI renvoie déjà notre schéma unifié, on passe-through
    if ($httpCode >= 200 && $httpCode < 300) {
        $decoded = json_decode($response, true);
        if (json_last_error() === JSON_ERROR_NONE) {
            echo json_encode($decoded);
        } else {
            echo json_encode(["status" => "success", "message" => "OK", "raw" => $response]);
        }
        exit;
    }

    // Erreurs FastAPI
    $decoded = json_decode($response, true);
    http_response_code($httpCode ?: 500);
    echo json_encode([
        "status"  => "error",
        "message" => $decoded['message'] ?? $decoded['detail'] ?? "Erreur côté FastAPI",
        "raw"     => $decoded ?: $response
    ]);
    exit;

} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(["status" => "error", "message" => $e->getMessage()]);
} finally {
    if (isset($conn) && $conn instanceof mysqli) {
        $conn->close();
    }
}