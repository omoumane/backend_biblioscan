<?php
include 'config.php';
include 'verify_token.php';

$user_id = verifyToken($conn);

if (!$user_id) {
    echo json_encode(["status" => "error", "message" => "Token invalide ou expiré"]);
    exit();
}

$stmt = $conn->prepare("DELETE FROM user_tokens WHERE user_id = ?");
$stmt->bind_param("i", $user_id);
$stmt->execute();

echo json_encode(["status" => "success", "message" => "Déconnecté avec succès"]);

$conn->close();
?>
