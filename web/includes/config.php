<?php
/**
 * Aurex Bank Statement Intelligence - Web Application
 * Configuration File
 */

// Error Reporting (controlled by environment)
$displayErrors = getenv('PHP_DISPLAY_ERRORS') === 'true' ? 1 : 0;
ini_set('display_errors', $displayErrors);
ini_set('display_startup_errors', $displayErrors);
error_reporting($displayErrors ? E_ALL : 0);

// Application Settings
define('APP_NAME', 'Aurex - Bank Statement Intelligence');
define('APP_VERSION', '1.0.0');
define('BASE_PATH', dirname(__DIR__));
define('PUBLIC_PATH', BASE_PATH . '/public');

// API Configuration
define('API_BASE_URL', getenv('API_BASE_URL') ?: 'http://localhost:8000');
define('API_TIMEOUT', 30);

// Session Configuration
define('SESSION_LIFETIME', 28800); // 8 hours
ini_set('session.gc_maxlifetime', SESSION_LIFETIME);
session_set_cookie_params(SESSION_LIFETIME);

// Security Settings
define('SECURE_COOKIES', getenv('SECURE_COOKIES') === 'true');
define('CSRF_TOKEN_LENGTH', 32);

// SSO Configuration
define('SSO_ENABLED', getenv('SSO_ENABLED') === 'true');
define('SSO_PROVIDER', getenv('SSO_PROVIDER') ?: 'oauth'); // oauth or saml
define('OAUTH_CLIENT_ID', getenv('OAUTH_CLIENT_ID') ?: '');
define('OAUTH_CLIENT_SECRET', getenv('OAUTH_CLIENT_SECRET') ?: '');
define('OAUTH_REDIRECT_URI', getenv('OAUTH_REDIRECT_URI') ?: '');
define('SAML_IDP_URL', getenv('SAML_IDP_URL') ?: '');
define('SAML_SP_ENTITY_ID', getenv('SAML_SP_ENTITY_ID') ?: '');

// File Upload Settings
define('MAX_FILE_SIZE', 50 * 1024 * 1024); // 50MB
define('ALLOWED_FILE_TYPES', ['pdf']);
define('UPLOAD_PATH', BASE_PATH . '/uploads');

// Database Settings (for session storage)
define('DB_PATH', BASE_PATH . '/data/sessions.db');

// Timezone
date_default_timezone_set('UTC');

// Start session
session_start();
