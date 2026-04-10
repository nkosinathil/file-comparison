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
        // TODO: Fetch from database
        $this->json([
            'cases' => [],
            'total' => 0
        ]);
    }
    
    public function show(string $id): void
    {
        // TODO: Fetch case from database
        $this->json([
            'id' => $id,
            'status' => 'pending'
        ]);
    }
    
    public function create(): void
    {
        $input = $this->getInput();
        
        // TODO: Validate input
        // TODO: Create case in database
        // TODO: Call Python backend to initialize processing
        
        $this->json([
            'id' => uniqid('CASE'),
            'message' => 'Case created successfully'
        ], 201);
    }
    
    public function process(string $id): void
    {
        // TODO: Trigger Python backend processing
        $this->json([
            'message' => 'Processing started',
            'case_id' => $id
        ]);
    }
    
    public function status(string $id): void
    {
        // TODO: Get processing status from Python backend
        $this->json([
            'case_id' => $id,
            'status' => 'processing',
            'progress' => 0
        ]);
    }
}
