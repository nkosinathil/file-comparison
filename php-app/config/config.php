<?php
/**
 * Aurex Configuration
 */

declare(strict_types=1);

// Load environment variables
if (file_exists(__DIR__ . '/../../.env')) {
    $lines = file(__DIR__ . '/../../.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        if (strpos($line, '=') === false) {
            continue;
        }
        list($name, $value) = explode('=', $line, 2);
        $value = trim($value);
        if (
            (str_starts_with($value, '"') && str_ends_with($value, '"')) ||
            (str_starts_with($value, "'") && str_ends_with($value, "'"))
        ) {
            $value = substr($value, 1, -1);
        }
        $_ENV[trim($name)] = $value;
    }
}

define('CONFIG', [
    'app_name' => $_ENV['APP_NAME'] ?? 'Aurex',
    'app_url' => $_ENV['APP_URL'] ?? 'http://localhost',
    'debug' => filter_var($_ENV['DEBUG'] ?? false, FILTER_VALIDATE_BOOLEAN),
    
    // Database
    'db_host' => $_ENV['DB_HOST'] ?? 'localhost',
    'db_port' => $_ENV['DB_PORT'] ?? '5432',
    'db_name' => $_ENV['DB_NAME'] ?? 'aurex',
    'db_user' => $_ENV['DB_USER'] ?? 'aurex',
    'db_pass' => $_ENV['DB_PASS'] ?? '',
    
    // Python Backend API
    'python_api_url' => $_ENV['PYTHON_API_URL'] ?? 'http://localhost:8000',
    'python_api_key' => $_ENV['PYTHON_API_KEY'] ?? '',
    
    // OIDC Configuration
    'oidc_enabled' => filter_var($_ENV['OIDC_ENABLED'] ?? false, FILTER_VALIDATE_BOOLEAN),
    'oidc_issuer' => $_ENV['OIDC_ISSUER'] ?? '',
    'oidc_client_id' => $_ENV['OIDC_CLIENT_ID'] ?? '',
    'oidc_client_secret' => $_ENV['OIDC_CLIENT_SECRET'] ?? '',
    'oidc_redirect_uri' => $_ENV['OIDC_REDIRECT_URI'] ?? '',
    
    // Session
    'session_lifetime' => (int)($_ENV['SESSION_LIFETIME'] ?? 7200),
    'session_name' => $_ENV['SESSION_NAME'] ?? 'AUREX_SESSION',
    
    // Upload
    'upload_max_size' => (int)($_ENV['UPLOAD_MAX_SIZE'] ?? 52428800), // 50MB
    'upload_allowed_types' => ['pdf'],
    'upload_path' => $_ENV['UPLOAD_PATH'] ?? '/var/aurex/uploads',
    
    // Case Storage
    'case_storage_path' => $_ENV['CASE_STORAGE_PATH'] ?? '/var/aurex/cases',
]);
