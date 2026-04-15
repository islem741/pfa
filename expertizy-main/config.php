<?php
/**
 * Application configuration
 * 
 * Database credentials are loaded from environment variables.
 * Copy .env.example to .env and fill in your values.
 * NEVER commit .env to version control.
 */

// Load .env file if it exists
$envFile = __DIR__ . '/.env';
if (file_exists($envFile)) {
    $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        // Skip comments
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        if (strpos($line, '=') !== false) {
            list($key, $value) = explode('=', $line, 2);
            $key = trim($key);
            $value = trim($value);
            if (!getenv($key)) {
                putenv("$key=$value");
            }
        }
    }
}

// Database configuration from environment variables
define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_NAME', getenv('DB_NAME') ?: 'expertizy');
define('DB_USERNAME', getenv('DB_USERNAME') ?: '');
define('DB_PASSWORD', getenv('DB_PASSWORD') ?: '');

/**
 * Get a PDO database connection with secure defaults.
 *
 * @return PDO
 */
function getDbConnection() {
    try {
        $pdo = new PDO(
            "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
            DB_USERNAME,
            DB_PASSWORD,
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]
        );
        return $pdo;
    } catch (PDOException $e) {
        // Log the real error server-side (when logging is configured)
        error_log("Database connection error: " . $e->getMessage());
        // Show a generic message to the user
        die("Une erreur interne est survenue. Veuillez réessayer plus tard.");
    }
}

/**
 * Configure secure session settings and start the session.
 */
function initSecureSession() {
    if (session_status() === PHP_SESSION_NONE) {
        // Set secure session cookie parameters
        session_set_cookie_params([
            'lifetime' => 0,           // Session cookie (expires when browser closes)
            'path' => '/',
            'domain' => '',
            'secure' => isset($_SERVER['HTTPS']),  // Only over HTTPS when available
            'httponly' => true,         // Prevent JavaScript access to session cookie
            'samesite' => 'Strict',    // Prevent CSRF via cross-site requests
        ]);
        session_start();
    }
}

/**
 * Generate or retrieve the current CSRF token.
 *
 * @return string
 */
function getCsrfToken() {
    initSecureSession();
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

/**
 * Validate a submitted CSRF token against the session token.
 *
 * @param string $token The token submitted with the form
 * @return bool
 */
function validateCsrfToken($token) {
    initSecureSession();
    if (empty($_SESSION['csrf_token']) || empty($token)) {
        return false;
    }
    return hash_equals($_SESSION['csrf_token'], $token);
}

/**
 * Sanitize a string for safe storage and display.
 *
 * @param string $input
 * @return string
 */
function sanitizeInput($input) {
    return htmlspecialchars(trim($input), ENT_QUOTES, 'UTF-8');
}

/**
 * Validate password strength.
 * Requires: minimum 8 characters, at least one uppercase letter,
 * one lowercase letter, and one digit.
 *
 * @param string $password
 * @return string|null Error message if invalid, null if valid
 */
function validatePassword($password) {
    if (strlen($password) < 8) {
        return "Le mot de passe doit contenir au moins 8 caractères.";
    }
    if (!preg_match('/[A-Z]/', $password)) {
        return "Le mot de passe doit contenir au moins une lettre majuscule.";
    }
    if (!preg_match('/[a-z]/', $password)) {
        return "Le mot de passe doit contenir au moins une lettre minuscule.";
    }
    if (!preg_match('/[0-9]/', $password)) {
        return "Le mot de passe doit contenir au moins un chiffre.";
    }
    return null;
}
