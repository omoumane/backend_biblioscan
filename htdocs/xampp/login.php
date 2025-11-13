<?php
$servername = "localhost";
$username = "root"; // Par défaut sur XAMPP
$password = ""; // Aucun mot de passe par défaut
$dbname = "diag_db";

// Connexion à la base de données
$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die(json_encode(["status" => "error", "message" => "Échec de connexion à la base de données"]));
}

// Vérifier si la requête est POST
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $identifiant = $_POST["identifiant"];
    $password = $_POST["password"];

    // Vérifier si l'utilisateur existe
    $stmt = $conn->prepare("SELECT password FROM users WHERE identifiant = ?");
    $stmt->bind_param("s", $identifiant);
    $stmt->execute();
    $stmt->store_result();
    
    if ($stmt->num_rows > 0) {
        $stmt->bind_result($db_password);
        $stmt->fetch();

        if ($password === $db_password) { 
            echo json_encode(["status" => "success", "message" => "Connexion réussie"]);
        } else {
            echo json_encode(["status" => "error", "message" => "Mot de passe incorrect"]);
        }
    } else {
        echo json_encode(["status" => "error", "message" => "Identifiant non trouvé"]);
    }

    $stmt->close();
}
$conn->close();
?>
