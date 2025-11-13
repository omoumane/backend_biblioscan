<?php
$host = "localhost";
$user = "root";
$pass = "";
$db = "bibliodb";

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
    die(json_encode(["status" => "error", "message" => "Erreur de connexion BD"]));
}

$conn->set_charset("utf8");
?>
