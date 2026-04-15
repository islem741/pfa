<?php
// Load shared configuration
require_once __DIR__ . '/config.php';

// Initialize secure session
initSecureSession();

// Process form submission
if (isset($_POST['nom']) && isset($_POST['prenom']) && isset($_POST['email']) && isset($_POST['password']) && isset($_POST['confirm_password']) && isset($_POST['account_type'])) {

    // Variables for messages
    $message = "";
    $message_type = "";

    // Validate CSRF token
    if (!validateCsrfToken($_POST['csrf_token'] ?? '')) {
        $message = "Requête invalide. Veuillez réessayer.";
        $message_type = "error";
    } else {
        // Sanitize inputs
        $nom = sanitizeInput($_POST['nom']);
        $prenom = sanitizeInput($_POST['prenom']);
        $email = filter_var(trim($_POST['email']), FILTER_SANITIZE_EMAIL);
        $password = $_POST['password'];
        $confirm_password = $_POST['confirm_password'];
        $account_type = sanitizeInput($_POST['account_type']);

        // Basic validation
        if (empty($nom) || empty($prenom) || empty($email) || empty($password) || empty($account_type)) {
            $message = "Tous les champs obligatoires doivent être remplis.";
            $message_type = "error";
        } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $message = "L'adresse email n'est pas valide.";
            $message_type = "error";
        } elseif ($password !== $confirm_password) {
            $message = "Les mots de passe ne correspondent pas.";
            $message_type = "error";
        } elseif (!in_array($account_type, ['user', 'expert'])) {
            $message = "Type de compte invalide.";
            $message_type = "error";
        } else {
            // Validate password strength
            $passwordError = validatePassword($password);
            if ($passwordError !== null) {
                $message = $passwordError;
                $message_type = "error";
            } else {
                try {
                    $pdo = getDbConnection();

                    // Check if email already exists
                    $stmt = $pdo->prepare("SELECT id FROM users WHERE email = ?");
                    $stmt->execute([$email]);

                    if ($stmt->fetch()) {
                        $message = "Cet email est déjà utilisé.";
                        $message_type = "error";
                    } else {
                        // Hash the password
                        $hashed_password = password_hash($password, PASSWORD_DEFAULT);

                        // Begin transaction
                        $pdo->beginTransaction();

                        // Insert user
                        $stmt = $pdo->prepare("INSERT INTO users (nom, prenom, email, password, account_type) VALUES (?, ?, ?, ?, ?)");
                        $stmt->execute([$nom, $prenom, $email, $hashed_password, $account_type]);
                        $user_id = $pdo->lastInsertId();

                        // Handle expert-specific data
                        if ($account_type === 'expert') {
                            if (isset($_POST['specialite']) && isset($_POST['experience']) && isset($_POST['diplomes']) && isset($_POST['tarif'])) {
                                $specialite = sanitizeInput($_POST['specialite']);
                                $experience = (int) $_POST['experience'];
                                $diplomes = sanitizeInput($_POST['diplomes']);
                                $tarif = (float) $_POST['tarif'];

                                // Validate expert fields
                                $valid_specialites = ['sante', 'commerce', 'rh', 'marketing', 'formation', 'juridique'];
                                if (empty($specialite) || !in_array($specialite, $valid_specialites) || empty($diplomes) || $experience < 0 || $tarif < 0) {
                                    throw new Exception("Tous les champs experts doivent être remplis correctement.");
                                }

                                // Insert into experts table
                                $stmt = $pdo->prepare("INSERT INTO experts (user_id, specialite, experience, diplomes, tarif_horaire) VALUES (?, ?, ?, ?, ?)");
                                $stmt->execute([$user_id, $specialite, $experience, $diplomes, $tarif]);

                                $message = "Compte expert créé avec succès ! Vous pouvez maintenant vous connecter.";
                                $message_type = "success";
                            } else {
                                throw new Exception("Les informations professionnelles sont requises pour un compte expert.");
                            }
                        } else {
                            $message = "Compte utilisateur créé avec succès ! Vous pouvez maintenant vous connecter.";
                            $message_type = "success";
                        }

                        // Commit transaction
                        $pdo->commit();
                    }
                } catch (Exception $e) {
                    if (isset($pdo) && $pdo->inTransaction()) {
                        $pdo->rollBack();
                    }
                    error_log("Signup error: " . $e->getMessage());
                    $message = "Erreur lors de la création du compte. Veuillez réessayer.";
                    $message_type = "error";
                }
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
    <title>Inscription</title>
    <link rel="stylesheet" href="stylessignup.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Raleway:wght@100;200;400;500&display=swap">
    <style>
        .hidden { display: none; }
        .error-message {
            background-color: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 5px solid #c62828;
        }
        .success-message {
            background-color: #e8f5e8;
            color: #2e7d32;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 5px solid #2e7d32;
        }
    </style>
</head>
<body>
    <script>
        function toggleExpertFields() {
            const accountType = document.getElementById('account-type').value;
            const expertFields = document.getElementById('expert-fields');
            
            if (accountType === 'expert') {
                expertFields.classList.remove('hidden');
            } else {
                expertFields.classList.add('hidden');
            }
        }
        
        // Fonction pour afficher/masquer les champs experts au chargement de la page
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('account-type').addEventListener('change', toggleExpertFields);
            // Vérifier l'état initial
            toggleExpertFields();
        });
    </script>
    
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

    <section>
        <div class="signup-container">
            <h2>Créer un compte</h2>
            
            <!-- Affichage des messages -->
            <?php if (isset($message) && !empty($message)): ?>
                <div class="<?php echo $message_type; ?>-message">
                    <?php echo htmlspecialchars($message); ?>
                </div>
            <?php endif; ?>
            
            <form id="signup-form" method="POST" action="signup.php">
                <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars(getCsrfToken()); ?>">
                
                <!-- Common fields -->
                <div class="form-group">
                    <label for="nom">Nom*</label>
                    <input type="text" name="nom" id="nom" value="<?php echo isset($_POST['nom']) ? htmlspecialchars($_POST['nom']) : ''; ?>" required>
                </div>
                
                <div class="form-group">
                    <label for="prenom">Prénom*</label>
                    <input type="text" name="prenom" id="prenom" value="<?php echo isset($_POST['prenom']) ? htmlspecialchars($_POST['prenom']) : ''; ?>" required>
                </div>

                <div class="form-group">
                    <label for="email">Email*</label>
                    <input type="email" name="email" id="email" value="<?php echo isset($_POST['email']) ? htmlspecialchars($_POST['email']) : ''; ?>" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Mot de passe*</label>
                    <input type="password" name="password" id="password" required minlength="8">
                    <small>Minimum 8 caractères, avec au moins une majuscule, une minuscule et un chiffre.</small>
                </div>
                
                <div class="form-group">
                    <label for="confirm_password">Confirmez le mot de passe*</label>
                    <input type="password" name="confirm_password" id="confirm_password" required>
                </div>
                
                <!-- Account type selector -->
                <div class="form-group">
                    <label for="account-type">Je suis*</label>
                    <select id="account-type" name="account_type" required>
                        <option value="">-- Sélectionnez --</option>
                        <option value="user" <?php echo (isset($_POST['account_type']) && $_POST['account_type'] === 'user') ? 'selected' : ''; ?>>Utilisateur</option>
                        <option value="expert" <?php echo (isset($_POST['account_type']) && $_POST['account_type'] === 'expert') ? 'selected' : ''; ?>>Expert</option>
                    </select>
                </div>
                
                <!-- Expert-specific fields -->
                <div id="expert-fields" class="<?php echo (isset($_POST['account_type']) && $_POST['account_type'] === 'expert') ? '' : 'hidden'; ?>">
                    <h3>Informations professionnelles</h3>
                    
                    <div class="form-group">
                        <label for="specialite">Spécialité*</label>
                        <select name="specialite" id="specialite">
                            <option value="">-- Sélectionnez votre spécialité --</option>
                            <option value="sante" <?php echo (isset($_POST['specialite']) && $_POST['specialite'] === 'sante') ? 'selected' : ''; ?>>Santé</option>
                            <option value="commerce" <?php echo (isset($_POST['specialite']) && $_POST['specialite'] === 'commerce') ? 'selected' : ''; ?>>Commerce</option>
                            <option value="rh" <?php echo (isset($_POST['specialite']) && $_POST['specialite'] === 'rh') ? 'selected' : ''; ?>>Ressources Humaines</option>
                            <option value="marketing" <?php echo (isset($_POST['specialite']) && $_POST['specialite'] === 'marketing') ? 'selected' : ''; ?>>Marketing Digital</option>
                            <option value="formation" <?php echo (isset($_POST['specialite']) && $_POST['specialite'] === 'formation') ? 'selected' : ''; ?>>Formation Professionnelle</option>
                            <option value="juridique" <?php echo (isset($_POST['specialite']) && $_POST['specialite'] === 'juridique') ? 'selected' : ''; ?>>Consultation Juridique</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="experience">Années d'expérience*</label>
                        <input type="number" name="experience" id="experience" min="0" value="<?php echo isset($_POST['experience']) ? htmlspecialchars($_POST['experience']) : ''; ?>">
                    </div>
                    
                    <div class="form-group">
                        <label for="diplomes">Diplômes/Certifications*</label>
                        <textarea name="diplomes" id="diplomes" rows="4"><?php echo isset($_POST['diplomes']) ? htmlspecialchars($_POST['diplomes']) : ''; ?></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="tarif">Tarif horaire (DT)*</label>
                        <input type="number" name="tarif" id="tarif" min="0" step="0.01" value="<?php echo isset($_POST['tarif']) ? htmlspecialchars($_POST['tarif']) : ''; ?>">
                    </div>
                </div>
                
                <button type="submit" class="btn-signup">S'inscrire</button>
            </form>
        </div>
    </section>
</body>
</html>
