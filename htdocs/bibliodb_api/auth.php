<?php
include 'config.php';

$data = json_decode(file_get_contents("php://input"), true);
$username = trim($data["username"] ?? '');
$password = trim($data["password"] ?? '');

if (empty($username) || empty($password)) {
    echo json_encode(["status" => "error", "message" => "Champs manquants"]);
    exit;
}

$stmt = $conn->prepare("SELECT user_id, password FROM users WHERE username = ?");
$stmt->bind_param("s", $username);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows === 1) {
    $row = $result->fetch_assoc();

    if (password_verify($password, $row["password"])) {
        $user_id = $row["user_id"];

        $token = bin2hex(random_bytes(32));
        $expires_at = date("Y-m-d H:i:s", strtotime("+10 minutes"));

        $conn->query("DELETE FROM user_tokens WHERE user_id = $user_id");

        $stmt = $conn->prepare("INSERT INTO user_tokens (user_id, token, expires_at) VALUES (?, ?, ?)");
        $stmt->bind_param("iss", $user_id, $token, $expires_at);
        $stmt->execute();

        echo json_encode([
            "status" => "success",
            "message" => "Connexion réussie",
            "token" => $token,
            "user_id" => $user_id
        ]);
    } else {
        echo json_encode(["status" => "error", "message" => "Mot de passe incorrect"]);
    }
} else {
    echo json_encode(["status" => "error", "message" => "Utilisateur introuvable"]);
}

$conn->close();
?>