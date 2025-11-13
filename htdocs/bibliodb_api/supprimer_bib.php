<?php
include 'config.php';
include 'verify_token.php';

$data = json_decode(file_get_contents("php://input"), true);
$biblio_id = isset($data["biblio_id"]) ? intval($data["biblio_id"]) : 0;
$user_id = verifyToken($conn);

if ($biblio_id <= 0 || $user_id <= 0) {
    echo json_encode(["status" => "error", "message" => "Paramètres invalides"]);
    exit();
}

$check = $conn->prepare("SELECT biblio_id FROM bibliotheques WHERE biblio_id = ? AND user_id = ?");
$check->bind_param("ii", $biblio_id, $user_id);
$check->execute();
$result = $check->get_result();

if ($result->num_rows === 0) {
    echo json_encode(["status" => "error", "message" => "Bibliothèque non trouvée ou accès refusé"]);
    exit();
}

$stmt = $conn->prepare("DELETE FROM bibliotheques WHERE biblio_id = ?");
$stmt->bind_param("i", $biblio_id);

if ($stmt->execute()) {
    echo json_encode(["status" => "success", "message" => "Bibliothèque supprimée avec succès"]);
} else {
    echo json_encode(["status" => "error", "message" => "Erreur lors de la suppression"]);
}

$conn->close();
?>
