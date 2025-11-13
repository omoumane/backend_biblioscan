<?php
include 'config.php';
include 'verify_token.php';

$data = json_decode(file_get_contents("php://input"), true);
$user_id = verifyToken($conn);


$biblio_id = (int)$data["biblio_id"];
$titre = $data["titre"];
$auteur = $data["auteur"];
$date_pub = $data["date_pub"];
$ligne = (int)$data["position_ligne"];
$colonne = (int)$data["position_colonne"];

$stmt = $conn->prepare("INSERT INTO livres (biblio_id, titre, auteur, date_pub, position_ligne, position_colonne) VALUES (?, ?, ?, ?, ?, ?)");
$stmt->bind_param("isssii", $biblio_id, $titre, $auteur, $date_pub, $ligne, $colonne);

if ($stmt->execute()) {
    echo json_encode(["status" => "success"]);
} else {
    echo json_encode(["status" => "error", "message" => "Erreur ajout livre"]);
}

$conn->close();
?>
