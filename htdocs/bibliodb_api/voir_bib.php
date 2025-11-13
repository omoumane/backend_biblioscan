<?php
include 'config.php';
include 'verify_token.php';

$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data["biblio_id"])) {
    echo json_encode(["error" => "biblio_id manquant"]);
    exit;
}

$biblio_id = $data["biblio_id"];
$user_id = verifyToken($conn);

$stmt = $conn->prepare("SELECT * FROM livres WHERE biblio_id = ?");
$stmt->bind_param("i", $biblio_id);
$stmt->execute();
$result = $stmt->get_result();

$livres = [];
while ($row = $result->fetch_assoc()) {
    $livres[] = $row;
}

echo json_encode($livres);
$conn->close();
?>
