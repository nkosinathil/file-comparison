<?php
/**
 * Login Page
 */
require_once __DIR__ . '/../includes/config.php';
require_once __DIR__ . '/../includes/auth.php';
require_once __DIR__ . '/../includes/api_client.php';

// Redirect if already authenticated
if (isAuthenticated()) {
    redirect('/dashboard.php');
}

$error = null;
$ssoEnabled = SSO_ENABLED;

// Handle login form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = sanitize($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    
    if (empty($username) || empty($password)) {
        $error = 'Please enter both username and password';
    } else {
        try {
            $api = new APIClient();
            $response = $api->login($username, $password);
            
            if (isset($response['access_token'])) {
                setAuth($response['access_token'], $response['user']);
                
                // Redirect to original destination or dashboard
                $redirect = $_SESSION['redirect_after_login'] ?? '/dashboard.php';
                unset($_SESSION['redirect_after_login']);
                redirect($redirect);
            } else {
                $error = 'Login failed: Invalid response from server';
            }
        } catch (Exception $e) {
            $error = 'Login failed: ' . $e->getMessage();
        }
    }
}

// Handle SSO initiation
if (isset($_GET['sso']) && $ssoEnabled) {
    if (SSO_PROVIDER === 'oauth') {
        try {
            $api = new APIClient();
            $result = $api->initiateOAuth(OAUTH_CLIENT_ID, OAUTH_REDIRECT_URI);
            redirect($result['authorization_url']);
        } catch (Exception $e) {
            $error = 'SSO initiation failed: ' . $e->getMessage();
        }
    }
}

$pageTitle = 'Login';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $pageTitle . ' - ' . APP_NAME; ?></title>
    <link rel="stylesheet" href="/assets/css/bootstrap.min.css">
    <link rel="stylesheet" href="/assets/css/fontawesome.min.css">
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-6 col-lg-5">
                <div class="card shadow-lg">
                    <div class="card-body p-5">
                        <div class="text-center mb-4">
                            <h1 class="h3 mb-3 fw-normal">
                                <i class="fas fa-chart-line text-primary"></i>
                                <?php echo APP_NAME; ?>
                            </h1>
                            <p class="text-muted">Sign in to your account</p>
                        </div>
                        
                        <?php if ($error): ?>
                            <div class="alert alert-danger" role="alert">
                                <i class="fas fa-exclamation-triangle"></i>
                                <?php echo htmlspecialchars($error); ?>
                            </div>
                        <?php endif; ?>
                        
                        <form method="POST" action="">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="fas fa-user"></i>
                                    </span>
                                    <input type="text" 
                                           class="form-control" 
                                           id="username" 
                                           name="username" 
                                           required 
                                           autofocus
                                           value="<?php echo isset($_POST['username']) ? htmlspecialchars($_POST['username']) : ''; ?>">
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="fas fa-lock"></i>
                                    </span>
                                    <input type="password" 
                                           class="form-control" 
                                           id="password" 
                                           name="password" 
                                           required>
                                </div>
                            </div>
                            
                            <div class="d-grid gap-2">
                                <button type="submit" class="btn btn-primary btn-lg">
                                    <i class="fas fa-sign-in-alt"></i> Sign In
                                </button>
                            </div>
                        </form>
                        
                        <?php if ($ssoEnabled): ?>
                            <div class="text-center my-3">
                                <span class="text-muted">or</span>
                            </div>
                            
                            <div class="d-grid">
                                <a href="?sso=1" class="btn btn-outline-primary">
                                    <i class="fas fa-sign-in-alt"></i> Sign in with SSO
                                </a>
                            </div>
                        <?php endif; ?>
                        
                        <div class="mt-4 text-center">
                            <small class="text-muted">
                                <strong>First Time Setup:</strong>
                                <br>
                                Check API server logs or <code>initial_admin_password.txt</code> file
                                <br>
                                for your randomly generated admin password.
                                <br>
                                <em>Change password immediately after login</em>
                            </small>
                        </div>
                    </div>
                </div>
                
                <div class="text-center mt-3 text-muted">
                    <small>Version <?php echo APP_VERSION; ?></small>
                </div>
            </div>
        </div>
    </div>
    
    <script src="/assets/js/bootstrap.bundle.min.js"></script>
</body>
</html>
