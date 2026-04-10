<?php
/**
 * Home Controller
 */

declare(strict_types=1);

namespace Aurex\Controllers;

class HomeController extends BaseController
{
    public function index(): void
    {
        $this->html('home', [
            'title' => 'Aurex - Bank Statement Intelligence',
            'app_name' => CONFIG['app_name']
        ]);
    }
}
