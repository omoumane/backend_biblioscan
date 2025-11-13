<?php
include 'config.php';
include 'verify_token.php';
$data = json_decode(file_get_contents("php://input"), true);

$user_id = verifyToken($conn);
$livre_id         = isset($data["livre_id"]) ? intval($data["livre_id"]) : 0;
$titre            = isset($data["titre"]) ? trim($data["titre"]) : "";
$auteur           = isset($data["auteur"]) ? trim($data["auteur"]) : "";
$date_pub         = isset($data["date_pub"]) ? trim($data["date_pub"]) : "";
$position_ligne   = isset($data["position_ligne"]) ? intval($data["position_ligne"]) : null;
$position_colonne = isset($data["position_colonne"]) ? intval($data["position_colonne"]) : null;

if ($user_id <= 0 || $livre_id <= 0) {
    echo json_encode(["status" => "error", "message" => "Paramètres invalides"]);
    exit();
}

// Vérifier l'accès (le livre appartient à l'utilisateur)
$check = $conn->prepare("
    SELECT l.livre_id 
    FROM livres l
    INNER JOIN bibliotheques b ON l.biblio_id = b.biblio_id
    WHERE l.livre_id = ? AND b.user_id = ?
");
$check->bind_param("ii", $livre_id, $user_id);
$check->execute();
$result = $check->get_result();

if ($result->num_rows === 0) {
    echo json_encode(["status" => "error", "message" => "Livre non trouvé ou accès refusé"]);
    exit();
}

$updateFields = [];
$params = [];
$types = "";

// --- Ajout des champs texte s'ils sont fournis (non vide) ---
if ($titre !== "") {
    $updateFields[] = "titre = ?";
    $params[] = $titre;
    $types .= "s";
}
if ($auteur !== "") {
    $updateFields[] = "auteur = ?";
    $params[] = $auteur;
    $types .= "s";
}
if ($date_pub !== "") {
    $updateFields[] = "date_pub = ?";
    $params[] = $date_pub;
    $types .= "s";
}

// --- Ajout des positions si fournies ---
if ($position_ligne !== null) {
    $updateFields[] = "position_ligne = ?";
    $params[] = $position_ligne;
    $types .= "i";
}
if ($position_colonne !== null) {
    $updateFields[] = "position_colonne = ?";
    $params[] = $position_colonne;
    $types .= "i";
}

if (empty($updateFields)) {
    echo json_encode(["status" => "error", "message" => "Aucun champ à modifier"]);
    exit();
}

// Fin: WHERE
$params[] = $livre_id;
$types .= "i";

$sql = "UPDATE livres SET " . implode(", ", $updateFields) . " WHERE livre_id = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param($types, ...$params);

if ($stmt->execute()) {
    if ($stmt->affected_rows > 0) {
        echo json_encode(["status" => "success", "message" => "Livre modifié avec succès"]);
    } else {
        echo json_encode(["status" => "success", "message" => "Aucune modification (valeurs identiques)"]);
    }
} else {
    echo json_encode(["status" => "error", "message" => "Erreur lors de la modification"]);
}

$conn->close();
