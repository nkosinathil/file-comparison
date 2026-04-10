<?php
/**
 * Base Controller
 */

declare(strict_types=1);

namespace Aurex\Controllers;

abstract class BaseController
{
    protected function json(array $data, int $status = 200): void
    {
        http_response_code($status);
        header('Content-Type: application/json');
        echo json_encode($data);
    }
    
    protected function html(string $view, array $data = []): void
    {
        extract($data);
        $viewPath = __DIR__ . "/../Views/{$view}.php";
        
        if (!file_exists($viewPath)) {
            throw new \Exception("View {$view} not found");
        }
        
        require $viewPath;
    }
    
    protected function getInput(): array
    {
        $contentType = $_SERVER['CONTENT_TYPE'] ?? '';
        
        if (strpos($contentType, 'application/json') !== false) {
            $json = file_get_contents('php://input');
            return json_decode($json, true) ?? [];
        }
        
        return array_merge($_GET, $_POST);
    }
    
    protected function requireAuth(): array
    {
        // TODO: Implement OIDC authentication
        // For now, return mock user
        if (!isset($_SESSION['user'])) {
            http_response_code(401);
            $this->json(['error' => 'Unauthorized']);
            exit;
        }
        
        return $_SESSION['user'];
    }
}
