<?php
header('Content-Type: application/json; charset=utf-8');

include 'config.php';
include 'verify_token.php'; // doit retourner l'user_id via le token

$data = json_decode(file_get_contents("php://input"), true);
$livre_id = isset($data["livre_id"]) ? intval($data["livre_id"]) : 0;

$user_id = verifyToken($conn); // Assure-toi que cette fonction lit bien le header

if ($user_id <= 0 || $livre_id <= 0) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Paramètres invalides"]);
    exit();
}

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
    http_response_code(403);
    echo json_encode(["status" => "error", "message" => "Livre non trouvé ou accès refusé"]);
    exit();
}

$stmt = $conn->prepare("DELETE FROM livres WHERE livre_id = ?");
$stmt->bind_param("i", $livre_id);

if ($stmt->execute()) {
    echo json_encode(["status" => "success", "message" => "Livre supprimé avec succès"]);
} else {
    http_response_code(500);
    echo json_encode(["status" => "error", "message" => "Erreur lors de la suppression"]);
}

$conn->close();
