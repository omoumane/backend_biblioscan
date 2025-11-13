<?php
include 'config.php';

$data = json_decode(file_get_contents("php://input"), true);
$username = trim($data["username"] ?? '');
$password = trim($data["password"] ?? '');
$nom      = trim($data["nom"] ?? '');
$prenom   = trim($data["prenom"] ?? '');

if (empty($username) || empty($password) || empty($nom) || empty($prenom)) {
    echo json_encode(["status" => "error", "message" => "Champs manquants"]);
    exit();
}

$hashedPassword = password_hash($password, PASSWORD_DEFAULT);

$check = $conn->prepare("SELECT user_id FROM users WHERE username = ?");
$check->bind_param("s", $username);
$check->execute();
$result = $check->get_result();

if ($result->num_rows > 0) {
    echo json_encode(["status" => "error", "message" => "Nom d'utilisateur déjà existant"]);
} else {
    $stmt = $conn->prepare("INSERT INTO users (username, password, nom, prenom) VALUES (?, ?, ?, ?)");
    $stmt->bind_param("ssss", $username, $hashedPassword, $nom, $prenom);

    if ($stmt->execute()) {
        echo json_encode([
            "status" => "success",
            "username" => $username,
            "nom" => $nom,
            "prenom" => $prenom
        ]);
    } else {
        echo json_encode(["status" => "error", "message" => "Erreur d'enregistrement"]);
    }
}

$conn->close();
?>
