<?php
// Load shared configuration
require_once __DIR__ . '/config.php';

// Initialize secure session
initSecureSession();

// Initialize variables
$email = $password = '';
$email_err = $password_err = $login_err = '';

// Process form submission
if ($_SERVER["REQUEST_METHOD"] == "POST") {

    // Validate CSRF token
    if (!validateCsrfToken($_POST['csrf_token'] ?? '')) {
        $login_err = "Requête invalide. Veuillez réessayer.";
    } else {
        // Validate email
        if (empty(trim($_POST["email"]))) {
            $email_err = "Veuillez entrer votre email.";
        } else {
            $email = trim($_POST["email"]);
        }

        // Validate password
        if (empty(trim($_POST["password"]))) {
            $password_err = "Veuillez entrer votre mot de passe.";
        } else {
            $password = trim($_POST["password"]);
        }

        // Authenticate
        if (empty($email_err) && empty($password_err)) {
            try {
                $pdo = getDbConnection();
                $stmt = $pdo->prepare("SELECT id, email, password, account_type FROM users WHERE email = ?");
                $stmt->execute([$email]);

                if ($user = $stmt->fetch()) {
                    if (password_verify($password, $user['password'])) {
                        // Regenerate session ID to prevent session fixation
                        session_regenerate_id(true);

                        // Store session data
                        $_SESSION["loggedin"] = true;
                        $_SESSION["id"] = $user['id'];
                        $_SESSION["email"] = $user['email'];
                        $_SESSION["account_type"] = $user['account_type'];

                        // Redirect based on account type
                        if ($user['account_type'] == 'expert') {
                            header("Location: dash-expert.php");
                            exit;
                        } else {
                            header("Location: dash-util.php");
                            exit;
                        }
                    } else {
                        $login_err = "Email ou mot de passe invalide.";
                    }
                } else {
                    $login_err = "Email ou mot de passe invalide.";
                }
            } catch (PDOException $e) {
                error_log("Login error: " . $e->getMessage());
                $login_err = "Une erreur interne est survenue. Veuillez réessayer plus tard.";
            }
        }
    }
}
?>
