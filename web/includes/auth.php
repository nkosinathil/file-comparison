<?php
/**
 * Authentication Helper Functions
 */

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return isset($_SESSION['user']) && isset($_SESSION['access_token']);
}

/**
 * Require authentication
 */
function requireAuth() {
    if (!isAuthenticated()) {
        $_SESSION['redirect_after_login'] = $_SERVER['REQUEST_URI'];
        header('Location: /login.php');
        exit;
    }
}

/**
 * Require admin role
 */
function requireAdmin() {
    requireAuth();
    if ($_SESSION['user']['role'] !== 'admin') {
        http_response_code(403);
        die('Access denied: Admin privileges required');
    }
}

/**
 * Get current user
 */
function getCurrentUser() {
    return isset($_SESSION['user']) ? $_SESSION['user'] : null;
}

/**
 * Get access token
 */
function getAccessToken() {
    return isset($_SESSION['access_token']) ? $_SESSION['access_token'] : null;
}

/**
 * Set authentication session
 */
function setAuth($token, $user) {
    $_SESSION['access_token'] = $token;
    $_SESSION['user'] = $user;
    $_SESSION['login_time'] = time();
}

/**
 * Clear authentication session
 */
function clearAuth() {
    unset($_SESSION['access_token']);
    unset($_SESSION['user']);
    unset($_SESSION['login_time']);
    session_destroy();
}

/**
 * Generate CSRF token
 */
function generateCSRFToken() {
    if (!isset($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(CSRF_TOKEN_LENGTH));
    }
    return $_SESSION['csrf_token'];
}

/**
 * Verify CSRF token
 */
function verifyCSRFToken($token) {
    return isset($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
}

/**
 * Get CSRF input field
 */
function csrfField() {
    $token = generateCSRFToken();
    return '<input type="hidden" name="csrf_token" value="' . htmlspecialchars($token) . '">';
}

/**
 * Sanitize input
 */
function sanitize($data) {
    if (is_array($data)) {
        return array_map('sanitize', $data);
    }
    return htmlspecialchars(strip_tags(trim($data)), ENT_QUOTES, 'UTF-8');
}

/**
 * Flash message functions
 */
function setFlashMessage($type, $message) {
    $_SESSION['flash_message'] = [
        'type' => $type,
        'message' => $message
    ];
}

function getFlashMessage() {
    if (isset($_SESSION['flash_message'])) {
        $flash = $_SESSION['flash_message'];
        unset($_SESSION['flash_message']);
        return $flash;
    }
    return null;
}

/**
 * Format file size
 */
function formatFileSize($bytes) {
    $units = ['B', 'KB', 'MB', 'GB', 'TB'];
    $bytes = max($bytes, 0);
    $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
    $pow = min($pow, count($units) - 1);
    $bytes /= (1 << (10 * $pow));
    return round($bytes, 2) . ' ' . $units[$pow];
}

/**
 * Format date/time
 */
function formatDateTime($datetime) {
    return date('Y-m-d H:i:s', strtotime($datetime));
}

/**
 * Redirect helper
 */
function redirect($url, $statusCode = 302) {
    header('Location: ' . $url, true, $statusCode);
    exit;
}

/**
 * JSON response helper
 */
function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit;
}

/**
 * Error response helper
 */
function errorResponse($message, $statusCode = 400) {
    jsonResponse(['error' => $message], $statusCode);
}
