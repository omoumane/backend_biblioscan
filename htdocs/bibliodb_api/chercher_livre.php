<?php
include 'config.php';
include 'verify_token.php';

$data = json_decode(file_get_contents("php://input"), true);

$user_id = verifyToken($conn);
$titre = "%" . ($data["titre"] ?? "") . "%";
$auteur = "%" . ($data["auteur"] ?? "") . "%";
$date = "%" . ($data["date_pub"] ?? "") . "%";

if ($user_id <= 0) {
    echo json_encode(["status" => "error", "message" => "Utilisateur non spécifié"]);
    exit();
}

$query = "
    SELECT l.*, b.nom AS nom_biblio
    FROM livres l
    JOIN bibliotheques b ON l.biblio_id = b.biblio_id
    WHERE b.user_id = ?
      AND l.titre LIKE ?
      AND l.auteur LIKE ?
      AND l.date_pub LIKE ?
";

$stmt = $conn->prepare($query);
$stmt->bind_param("isss", $user_id, $titre, $auteur, $date);
$stmt->execute();
$result = $stmt->get_result();

$livres = [];
while ($row = $result->fetch_assoc()) {
    $livres[] = $row;
}

if (count($livres) > 0) {
    echo json_encode(["status" => "success", "livres" => $livres]);
} else {
    echo json_encode(["status" => "empty", "message" => "Aucun livre trouvé"]);
}

$conn->close();
?>
