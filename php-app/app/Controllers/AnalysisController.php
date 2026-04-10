<?php
/**
 * Analysis Controller
 */

declare(strict_types=1);

namespace Aurex\Controllers;

class AnalysisController extends BaseController
{
    public function show(string $id): void
    {
        // TODO: Fetch analysis data from Python backend
        $this->json([
            'case_id' => $id,
            'insights' => [],
            'network' => [],
            'statistics' => []
        ]);
    }
}
