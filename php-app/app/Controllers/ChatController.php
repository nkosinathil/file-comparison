<?php
/**
 * Chat Controller
 */

declare(strict_types=1);

namespace Aurex\Controllers;

class ChatController extends BaseController
{
    public function ask(string $id): void
    {
        $input = $this->getInput();
        $question = $input['question'] ?? '';
        
        if (empty($question)) {
            $this->json(['error' => 'Question is required'], 400);
            return;
        }

        $response = $this->pythonApiRequest(
            'POST',
            '/api/chat/' . urlencode($id) . '/ask',
            ['question' => $question]
        );
        if (!$response['ok']) {
            $this->json(['error' => $response['error']], $response['status']);
            return;
        }

        $this->json($response['data']);
    }
}
