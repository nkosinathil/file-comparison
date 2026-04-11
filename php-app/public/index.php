<?php
/**
 * Aurex Web Application Entry Point
 * PHP MVC Front Controller
 */

declare(strict_types=1);

// Load configuration
require_once __DIR__ . '/../config/config.php';

// Autoloader
spl_autoload_register(function ($class) {
    $prefix = 'Aurex\\';
    $base_dir = __DIR__ . '/../app/';
    
    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }
    
    $relative_class = substr($class, $len);
    $file = $base_dir . str_replace('\\', '/', $relative_class) . '.php';
    
    if (file_exists($file)) {
        require $file;
    }
});

// Initialize Router
$router = new \Aurex\Router();

// Define routes
$router->get('/', 'HomeController@index');
$router->get('/cases', 'CaseController@list');
$router->get('/cases/{id}', 'CaseController@show');
$router->post('/cases', 'CaseController@create');
$router->post('/cases/{id}/process', 'CaseController@process');
$router->get('/cases/{id}/status', 'CaseController@status');
$router->get('/cases/{id}/analysis', 'AnalysisController@show');
$router->post('/cases/{id}/chat', 'ChatController@ask');
$router->get('/api/health', 'ApiController@health');

// Dispatch request
try {
    $router->dispatch($_SERVER['REQUEST_METHOD'], $_SERVER['REQUEST_URI']);
} catch (Exception $e) {
    http_response_code(500);
    if (CONFIG['debug']) {
        echo json_encode([
            'error' => 'Internal Server Error',
            'message' => $e->getMessage(),
            'trace' => $e->getTraceAsString()
        ]);
    } else {
        echo json_encode(['error' => 'Internal Server Error']);
    }
}
