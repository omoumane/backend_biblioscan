<?php
include 'config.php';
include 'verify_token.php';

$data = json_decode(file_get_contents("php://input"), true);
$nom = $data["nom"];
$nb_lignes = (int)$data["nb_lignes"];
$nb_colonnes = (int)$data["nb_colonnes"];
$user_id = verifyToken($conn);


$stmt = $conn->prepare("INSERT INTO bibliotheques (user_id, nom, nb_lignes, nb_colonnes) VALUES (?, ?, ?, ?)");
$stmt->bind_param("isii", $user_id, $nom, $nb_lignes, $nb_colonnes);

if ($stmt->execute()) {
    echo json_encode(["status" => "success"]);
} else {
    echo json_encode(["status" => "error", "message" => "Erreur création bibliothèque"]);
}

$conn->close();
?>
