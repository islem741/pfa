<?php
// Configuration de la base de données
define('DB_SERVER', 'localhost');
define('DB_USERNAME', 'votre_utilisateur');
define('DB_PASSWORD', 'votre_mot_de_passe');
define('DB_NAME', 'expertizy');

// Connexion à la base de données
$conn = mysqli_connect(DB_SERVER, DB_USERNAME, DB_PASSWORD, DB_NAME);

// Vérifier la connexion
if($conn === false){
    die("ERREUR : Impossible de se connecter. " . mysqli_connect_error());
}

// Initialiser les variables
$email = $password = '';
$email_err = $password_err = $login_err = '';

// Traitement du formulaire lorsqu'il est soumis
if($_SERVER["REQUEST_METHOD"] == "POST"){
    
    // Vérifier si l'email est vide
    if(empty(trim($_POST["email"]))){
        $email_err = "Veuillez entrer votre email.";
    } else{
        $email = trim($_POST["email"]);
    }
    
    // Vérifier si le mot de passe est vide
    if(empty(trim($_POST["password"]))){
        $password_err = "Veuillez entrer votre mot de passe.";
    } else{
        $password = trim($_POST["password"]);
    }
    
    // Valider les informations d'identification
    if(empty($email_err) && empty($password_err)){
        // Préparer une déclaration SELECT
        $sql = "SELECT id, email, password, account_type FROM users WHERE email = ?";
        
        if($stmt = mysqli_prepare($conn, $sql)){
            // Lier les variables à la déclaration préparée en tant que paramètres
            mysqli_stmt_bind_param($stmt, "s", $param_email);
            
            // Définir les paramètres
            $param_email = $email;
            
            // Tenter d'exécuter la déclaration préparée
            if(mysqli_stmt_execute($stmt)){
                // Stocker le résultat
                mysqli_stmt_store_result($stmt);
                
                // Vérifier si l'email existe, si oui alors vérifier le mot de passe
                if(mysqli_stmt_num_rows($stmt) == 1){                    
                    // Lier les variables de résultat
                    mysqli_stmt_bind_result($stmt, $id, $email, $hashed_password, $account_type);
                    if(mysqli_stmt_fetch($stmt)){
                        if(password_verify($password, $hashed_password)){
                            // Le mot de passe est correct, démarrer une nouvelle session
                            session_start();
                            
                            // Stocker les données dans les variables de session
                            $_SESSION["loggedin"] = true;
                            $_SESSION["id"] = $id;
                            $_SESSION["email"] = $email;                            
                            $_SESSION["account_type"] = $account_type;
                            
                            // Rediriger l'utilisateur vers la page appropriée
                            if($account_type == 'expert'){
                                header("location: dash-expert.php");
                            } else {
                                header("location: dash-util.php");
                            }
                        } else{
                            // Le mot de passe n'est pas valide
                            $login_err = "Email ou mot de passe invalide.";
                        }
                    }
                } else{
                    // L'email n'existe pas
                    $login_err = "Email ou mot de passe invalide.";
                }
            } else{
                echo "Oops! Quelque chose s'est mal passé. Veuillez réessayer plus tard.";
            }

            // Fermer la déclaration
            mysqli_stmt_close($stmt);
        }
    }
    
    // Fermer la connexion
    mysqli_close($conn);
}
?>