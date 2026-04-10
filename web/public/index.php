<?php
/**
 * Index - Redirect to appropriate page
 */
require_once __DIR__ . '/../includes/config.php';
require_once __DIR__ . '/../includes/auth.php';

if (isAuthenticated()) {
    redirect('/dashboard.php');
} else {
    redirect('/login.php');
}
