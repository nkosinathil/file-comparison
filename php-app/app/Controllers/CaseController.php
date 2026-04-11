<?php
/**
 * Case Controller
 */

declare(strict_types=1);

namespace Aurex\Controllers;

class CaseController extends BaseController
{
    public function list(): void
    {
        $query = [];
        if (isset($_GET['skip'])) {
            $query[] = 'skip=' . urlencode((string)$_GET['skip']);
        }
        if (isset($_GET['limit'])) {
            $query[] = 'limit=' . urlencode((string)$_GET['limit']);
        }
        if (isset($_GET['status'])) {
            $query[] = 'status=' . urlencode((string)$_GET['status']);
        }

        $path = '/api/cases/';
        if (!empty($query)) {
            $path .= '?' . implode('&', $query);
        }

        $response = $this->pythonApiRequest('GET', $path);
        if (!$response['ok']) {
            $this->json(['error' => $response['error']], $response['status']);
            return;
        }

        $this->json([
            'cases' => $response['data'],
            'total' => count($response['data'])
        ]);
    }
    
    public function show(string $id): void
    {
        $response = $this->pythonApiRequest('GET', '/api/cases/' . urlencode($id));
        if (!$response['ok']) {
            $this->json(['error' => $response['error']], $response['status']);
            return;
        }
        $this->json($response['data']);
    }
    
    public function create(): void
    {
        $input = $this->getInput();
        $requiredFields = ['case_name', 'input_folder', 'output_folder'];
        foreach ($requiredFields as $field) {
            if (empty($input[$field])) {
                $this->json(['error' => "{$field} is required"], 400);
                return;
            }
        }

        $response = $this->pythonApiRequest('POST', '/api/cases/', [
            'case_name' => (string)$input['case_name'],
            'evidence_number' => $input['evidence_number'] ?? null,
            'timezone' => $input['timezone'] ?? 'UTC',
            'input_folder' => (string)$input['input_folder'],
            'output_folder' => (string)$input['output_folder'],
        ]);
        if (!$response['ok']) {
            $this->json(['error' => $response['error']], $response['status']);
            return;
        }
        $this->json($response['data'], 201);
    }
    
    public function process(string $id): void
    {
        $response = $this->pythonApiRequest('POST', '/api/processing/' . urlencode($id) . '/start', []);
        if (!$response['ok']) {
            $this->json(['error' => $response['error']], $response['status']);
            return;
        }
        $this->json($response['data']);
    }
    
    public function status(string $id): void
    {
        $response = $this->pythonApiRequest('GET', '/api/processing/' . urlencode($id) . '/status');
        if (!$response['ok']) {
            $this->json(['error' => $response['error']], $response['status']);
            return;
        }
        $this->json($response['data']);
    }
}
