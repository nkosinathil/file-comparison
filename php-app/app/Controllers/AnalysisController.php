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
        $insights = $this->pythonApiRequest('GET', '/api/analysis/' . urlencode($id) . '/insights');
        $network = $this->pythonApiRequest('GET', '/api/analysis/' . urlencode($id) . '/network');
        $transactions = $this->pythonApiRequest('GET', '/api/analysis/' . urlencode($id) . '/transactions');

        if (!$insights['ok']) {
            $this->json(['error' => $insights['error']], $insights['status']);
            return;
        }
        if (!$network['ok']) {
            $this->json(['error' => $network['error']], $network['status']);
            return;
        }
        if (!$transactions['ok']) {
            $this->json(['error' => $transactions['error']], $transactions['status']);
            return;
        }

        $this->json([
            'case_id' => $id,
            'insights' => $insights['data'],
            'network' => $network['data'],
            'transactions' => $transactions['data']
        ]);
    }
}
