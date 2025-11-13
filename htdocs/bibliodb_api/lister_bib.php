<?php
include 'config.php';
include 'verify_token.php';

$user_id = verifyToken($conn);

if (!$user_id) {
    echo json_encode(["status" => "error", "message" => "Utilisateur non connecté"]);
    exit();
}

$stmt = $conn->prepare("SELECT biblio_id, nom, nb_lignes, nb_colonnes 
                        FROM bibliotheques 
                        WHERE user_id = ?");
$stmt->bind_param("i", $user_id);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    $bibliotheques = [];
    while ($row = $result->fetch_assoc()) {
        $bibliotheques[] = $row;
    }
    echo json_encode(["status" => "success", "bibliotheques" => $bibliotheques]);
} else {
    echo json_encode(["status" => "error", "message" => "Aucune bibliothèque trouvée"]);
}

$conn->close();
?>