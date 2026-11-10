<?php

$dbFile = __DIR__ . '/project.db';

try {
    $conn = new SQLite3($dbFile);
} catch (Exception $e) {
    die('Database connection failed: ' . $e->getMessage());
}

?>