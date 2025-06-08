<?php
// Configuration de la base de données
$host = "localhost";
$dbname = "pfa";
$username = "root";
$password = "";

// Connexion à la base de données
try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erreur de connexion : " . $e->getMessage());
}

// Vérifier si le formulaire a été soumis
if (isset($_POST['nom']) && isset($_POST['prenom']) && isset($_POST['email']) && isset($_POST['password']) && isset($_POST['confirm_password']) && isset($_POST['account_type'])) {
    
    // Récupérer les données du formulaire
    $nom = $_POST['nom'];
    $prenom = $_POST['prenom'];
    $email = $_POST['email'];
    $password = $_POST['password'];
    $confirm_password = $_POST['confirm_password'];
    $account_type = $_POST['account_type'];
    
    // Variables pour les messages
    $message = "";
    $message_type = "";
    
    // Validation basique
    if (empty($nom) || empty($prenom) || empty($email) || empty($password) || empty($account_type)) {
        $message = "Tous les champs obligatoires doivent être remplis.";
        $message_type = "error";
    }
    elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $message = "L'adresse email n'est pas valide.";
        $message_type = "error";
    }
    elseif ($password !== $confirm_password) {
        $message = "Les mots de passe ne correspondent pas.";
        $message_type = "error";
    }
    else {
        // Vérifier si l'email existe déjà
        $stmt = $pdo->prepare("SELECT id FROM users WHERE email = ?");
        $stmt->execute([$email]);
        
        if ($stmt->fetch()) {
            $message = "Cet email est déjà utilisé.";
            $message_type = "error";
        }
        else {
            // Hacher le mot de passe
            $hashed_password = password_hash($password, PASSWORD_DEFAULT);
            
            try {
                // Commencer une transaction
                $pdo->beginTransaction();
                
                // Insérer l'utilisateur
                $stmt = $pdo->prepare("INSERT INTO users (nom, prenom, email, password, account_type) VALUES (?, ?, ?, ?, ?)");
                $stmt->execute([$nom, $prenom, $email, $hashed_password, $account_type]);
                $user_id = $pdo->lastInsertId();
                
                // Si c'est un expert, traiter les données supplémentaires
                if ($account_type === 'expert') {
                    if (isset($_POST['specialite']) && isset($_POST['experience']) && isset($_POST['diplomes']) && isset($_POST['tarif'])) {
                        $specialite = $_POST['specialite'];
                        $experience = $_POST['experience'];
                        $diplomes = $_POST['diplomes'];
                        $tarif = $_POST['tarif'];
                        
                        // Validation des champs expert
                        if (empty($specialite) || empty($diplomes) || $experience < 0 || $tarif < 0) {
                            throw new Exception("Tous les champs experts doivent être remplis correctement.");
                        }
                        
                        // Insérer dans la table experts
                        $stmt = $pdo->prepare("INSERT INTO experts (user_id, specialite, experience, diplomes, tarif_horaire) VALUES (?, ?, ?, ?, ?)");
                        $stmt->execute([$user_id, $specialite, $experience, $diplomes, $tarif]);
                        
                        $message = "Compte expert créé avec succès ! Vous pouvez maintenant vous connecter.";
                        $message_type = "success";
                    }
                    else {
                        throw new Exception("Les informations professionnelles sont requises pour un compte expert.");
                    }
                }
                else {
                    $message = "Compte utilisateur créé avec succès ! Vous pouvez maintenant vous connecter.";
                    $message_type = "success";
                }
                
                // Valider la transaction
                $pdo->commit();
                
            } catch (Exception $e) {
                // Annuler la transaction en cas d'erreur
                $pdo->rollBack();
                $message = "Erreur lors de la création du compte : " . $e->getMessage();
                $message_type = "error";
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
                    <input type="password" name="password" id="password" required>
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