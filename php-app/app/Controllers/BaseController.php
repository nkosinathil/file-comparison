<?php
/**
 * Base Controller
 */

declare(strict_types=1);

namespace Aurex\Controllers;

abstract class BaseController
{
    protected function pythonApiRequest(
        string $method,
        string $path,
        ?array $payload = null
    ): array {
        $baseUrl = rtrim((string)CONFIG['python_api_url'], '/');
        $url = $baseUrl . '/' . ltrim($path, '/');

        $headers = [
            'Content-Type: application/json',
            'Accept: application/json',
        ];

        if (!empty(CONFIG['python_api_key'])) {
            $headers[] = 'X-API-Key: ' . CONFIG['python_api_key'];
        }

        $content = [
            'method' => strtoupper($method),
            'header' => implode("\r\n", $headers),
            'ignore_errors' => true,
            'timeout' => 30,
        ];

        if ($payload !== null) {
            $content['content'] = json_encode($payload);
        }

        $context = stream_context_create(['http' => $content]);
        $responseBody = @file_get_contents($url, false, $context);
        $statusCode = 0;

        if (isset($http_response_header[0])) {
            preg_match('{HTTP/\S+\s(\d{3})}', $http_response_header[0], $matches);
            $statusCode = isset($matches[1]) ? (int)$matches[1] : 0;
        }

        $decoded = null;
        if (is_string($responseBody) && $responseBody !== '') {
            $decoded = json_decode($responseBody, true);
        }

        if ($statusCode >= 400 || $responseBody === false) {
            $message = 'Python backend request failed';
            if (is_array($decoded) && isset($decoded['detail'])) {
                $message = (string)$decoded['detail'];
            } elseif (is_array($decoded) && isset($decoded['error'])) {
                $message = (string)$decoded['error'];
            }

            return [
                'ok' => false,
                'status' => $statusCode > 0 ? $statusCode : 502,
                'error' => $message,
                'data' => $decoded,
            ];
        }

        return [
            'ok' => true,
            'status' => $statusCode > 0 ? $statusCode : 200,
            'data' => is_array($decoded) ? $decoded : [],
        ];
    }

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
