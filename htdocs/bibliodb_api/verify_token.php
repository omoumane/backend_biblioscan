<?php
function verifyToken($conn) {
    $headers = getallheaders();

    if (!isset($headers['Authorization'])) {
        echo json_encode(["status" => "error", "message" => "Token manquant"]);
        exit;
    }

    $token = trim(str_replace('Bearer', '', $headers['Authorization']));

    $stmt = $conn->prepare("SELECT user_id, expires_at FROM user_tokens WHERE token = ?");
    $stmt->bind_param("s", $token);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows === 0) {
        echo json_encode(["status" => "error", "message" => "Token invalide"]);
        exit;
    }

    $row = $result->fetch_assoc();

    if (strtotime($row["expires_at"]) < time()) {
        $stmt = $conn->prepare("DELETE FROM user_tokens WHERE token = ?");
        $stmt->bind_param("s", $token);
        $stmt->execute();

        echo json_encode(["status" => "error", "message" => "Token expiré"]);
        exit;
    }

    $nouvelle_expiration = date("Y-m-d H:i:s", strtotime("+10 minutes"));
    $stmt = $conn->prepare("UPDATE user_tokens SET expires_at = ? WHERE token = ?");
    $stmt->bind_param("ss", $nouvelle_expiration, $token);
    $stmt->execute();
    
    return $row["user_id"];
}
?>