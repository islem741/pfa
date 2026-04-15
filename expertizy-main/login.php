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
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Expertizy</title>
    <link rel="stylesheet" href="styleslogin.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Raleway:wght@100;200;400;500&display=swap">
</head>
<body>
    <script src="script.js" defer></script>

    <header>
        <div class="logo">
            <a href="index.html"> <span>expert</span>IZY</a>
        </div>
        <ul class="menu">
            <li><a href="index.html">Accueil</a></li>
            <li><a href="#">À Propos</a></li>
            <li><a href="#">Contact</a></li>
        </ul>
    </header>

    <section class="login-section">
        <div id="login-container">
            <h2>Connexion</h2>
            
            <?php if (!empty($login_err)): ?>
                <div style="background-color: #ffebee; color: #c62828; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #c62828;">
                    <?php echo htmlspecialchars($login_err); ?>
                </div>
            <?php endif; ?>
            
            <div class="account-type-selector">
                <div class="selector-options">
                    <input type="radio" id="user-type" name="account-type" value="user" checked hidden>
                    <label for="user-type" class="option-card">
                        <div class="option-icon">👤</div>
                        <h3>Utilisateur</h3>
                        <p>Je cherche des experts</p>
                    </label>
                    
                    <input type="radio" id="expert-type" name="account-type" value="expert" hidden>
                    <label for="expert-type" class="option-card">
                        <div class="option-icon">⭐</div>
                        <h3>Expert</h3>
                        <p>Je propose mes services</p>
                    </label>
                </div>
            </div>
            
            <form action="login.php" method="POST">
                <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars(getCsrfToken()); ?>">
                
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" placeholder="votre@email.com" value="<?php echo htmlspecialchars($email); ?>" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Mot de passe</label>
                    <input type="password" id="password" name="password" placeholder="••••••••" required>
                </div>
                
                <button type="submit" class="btn-login">Se Connecter</button>
                
                <div class="forgot-password">
                    <a href="#">Mot de passe oublié ?</a>
                </div>
            </form>
            
            <div class="signup-link">
                <p>Pas encore de compte ? <a href="signup.php" class="btn-signup">S'inscrire</a></p>
            </div>
        </div>
    </section>

    <footer>
        <p>&copy; 2025 Expertizy. Tous droits réservés.</p>
    </footer>
</body>
</html>
