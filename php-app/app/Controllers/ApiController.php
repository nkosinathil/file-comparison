<?php
/**
 * API Controller
 */

declare(strict_types=1);

namespace Aurex\Controllers;

class ApiController extends BaseController
{
    public function health(): void
    {
        $this->json([
            'status' => 'healthy',
            'timestamp' => date('c'),
            'version' => '1.0.0'
        ]);
    }
}
