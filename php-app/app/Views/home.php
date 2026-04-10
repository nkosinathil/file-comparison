<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($title ?? 'Aurex') ?></title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: #E2E8F0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: rgba(15, 23, 42, 0.8);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid #334155;
        }
        h1 {
            color: #14B8A6;
            font-size: 2rem;
        }
        main {
            flex: 1;
            padding: 3rem 2rem;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }
        .card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid #334155;
        }
        .btn {
            background: #14B8A6;
            color: #0F172A;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #0D9488;
        }
    </style>
</head>
<body>
    <header>
        <h1><?= htmlspecialchars($app_name ?? 'Aurex') ?></h1>
    </header>
    <main>
        <div class="card">
            <h2>Welcome to Aurex Bank Statement Intelligence</h2>
            <p style="margin: 1rem 0;">A secure, web-based platform for analyzing bank statements with AI-powered insights.</p>
            <a href="/cases" class="btn">View Cases</a>
        </div>
        
        <div class="card">
            <h3>Features</h3>
            <ul style="margin-left: 1.5rem; line-height: 1.8;">
                <li>Secure OIDC authentication</li>
                <li>PDF statement processing</li>
                <li>AI-powered transaction analysis</li>
                <li>Network visualization</li>
                <li>Financial insights and reporting</li>
            </ul>
        </div>
    </main>
</body>
</html>
