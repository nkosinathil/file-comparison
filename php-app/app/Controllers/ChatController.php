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
        
        // TODO: Forward to Python backend AI chat service
        $this->json([
            'case_id' => $id,
            'question' => $question,
            'answer' => 'AI response placeholder'
        ]);
    }
}
