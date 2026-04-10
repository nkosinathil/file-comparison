<?php
/**
 * Logout Page
 */
require_once __DIR__ . '/../includes/config.php';
require_once __DIR__ . '/../includes/auth.php';

clearAuth();
setFlashMessage('success', 'You have been logged out successfully');
redirect('/login.php');
