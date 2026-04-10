<?php
/**
 * Dashboard Page
 */
require_once __DIR__ . '/../includes/config.php';
require_once __DIR__ . '/../includes/auth.php';
require_once __DIR__ . '/../includes/api_client.php';

requireAuth();

$api = new APIClient(API_BASE_URL, getAccessToken());
$pageTitle = 'Dashboard';

try {
    $cases = $api->getCases();
    $recentCases = array_slice($cases, 0, 5);
    $totalCases = count($cases);
    $completedCases = count(array_filter($cases, fn($c) => $c['status'] === 'completed'));
} catch (Exception $e) {
    setFlashMessage('error', 'Failed to load dashboard data: ' . $e->getMessage());
    $cases = [];
    $recentCases = [];
    $totalCases = 0;
    $completedCases = 0;
}

include __DIR__ . '/../templates/header.php';
?>

<div class="container-fluid mt-4">
    <div class="row mb-4">
        <div class="col">
            <h1><i class="fas fa-tachometer-alt"></i> Dashboard</h1>
            <p class="text-muted">Welcome back, <?php echo htmlspecialchars($_SESSION['user']['full_name']); ?></p>
        </div>
        <div class="col-auto">
            <a href="/new-case.php" class="btn btn-primary">
                <i class="fas fa-plus-circle"></i> New Case
            </a>
        </div>
    </div>
    
    <!-- Statistics Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="card-title text-white-50 mb-1">Total Cases</h6>
                            <h2 class="mb-0"><?php echo $totalCases; ?></h2>
                        </div>
                        <div class="fs-1 opacity-50">
                            <i class="fas fa-folder-open"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="card-title text-white-50 mb-1">Completed</h6>
                            <h2 class="mb-0"><?php echo $completedCases; ?></h2>
                        </div>
                        <div class="fs-1 opacity-50">
                            <i class="fas fa-check-circle"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card bg-warning text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="card-title text-white-50 mb-1">In Progress</h6>
                            <h2 class="mb-0"><?php echo count(array_filter($cases, fn($c) => $c['status'] === 'processing')); ?></h2>
                        </div>
                        <div class="fs-1 opacity-50">
                            <i class="fas fa-sync-alt"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="card-title text-white-50 mb-1">Total Transactions</h6>
                            <h2 class="mb-0"><?php echo array_sum(array_column($cases, 'total_transactions')); ?></h2>
                        </div>
                        <div class="fs-1 opacity-50">
                            <i class="fas fa-exchange-alt"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Recent Cases -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header bg-white">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-clock"></i> Recent Cases
                    </h5>
                </div>
                <div class="card-body">
                    <?php if (empty($recentCases)): ?>
                        <div class="text-center py-5 text-muted">
                            <i class="fas fa-folder-open fa-3x mb-3"></i>
                            <p>No cases found. Create your first case to get started.</p>
                            <a href="/new-case.php" class="btn btn-primary">
                                <i class="fas fa-plus-circle"></i> Create New Case
                            </a>
                        </div>
                    <?php else: ?>
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Case Name</th>
                                        <th>Evidence #</th>
                                        <th>Investigator</th>
                                        <th>Created</th>
                                        <th>Status</th>
                                        <th>Transactions</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php foreach ($recentCases as $case): ?>
                                        <tr>
                                            <td>
                                                <strong><?php echo htmlspecialchars($case['case_name']); ?></strong>
                                            </td>
                                            <td><?php echo htmlspecialchars($case['evidence_number']); ?></td>
                                            <td><?php echo htmlspecialchars($case['investigator']); ?></td>
                                            <td><?php echo formatDateTime($case['created_at']); ?></td>
                                            <td>
                                                <?php
                                                $statusClass = [
                                                    'completed' => 'success',
                                                    'processing' => 'warning',
                                                    'error' => 'danger',
                                                    'pending' => 'secondary'
                                                ];
                                                $class = $statusClass[$case['status']] ?? 'secondary';
                                                ?>
                                                <span class="badge bg-<?php echo $class; ?>">
                                                    <?php echo ucfirst($case['status']); ?>
                                                </span>
                                            </td>
                                            <td><?php echo number_format($case['total_transactions']); ?></td>
                                            <td>
                                                <a href="/case.php?id=<?php echo urlencode($case['case_id']); ?>" 
                                                   class="btn btn-sm btn-outline-primary">
                                                    <i class="fas fa-eye"></i> View
                                                </a>
                                            </td>
                                        </tr>
                                    <?php endforeach; ?>
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="text-center mt-3">
                            <a href="/cases.php" class="btn btn-outline-primary">
                                View All Cases <i class="fas fa-arrow-right"></i>
                            </a>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quick Actions -->
    <div class="row mt-4">
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-plus-circle fa-3x text-primary mb-3"></i>
                    <h5>Create New Case</h5>
                    <p class="text-muted">Start analyzing a new set of bank statements</p>
                    <a href="/new-case.php" class="btn btn-primary">Create Case</a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-folder-open fa-3x text-success mb-3"></i>
                    <h5>Browse Cases</h5>
                    <p class="text-muted">View and manage all your cases</p>
                    <a href="/cases.php" class="btn btn-success">Browse</a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-book fa-3x text-info mb-3"></i>
                    <h5>Documentation</h5>
                    <p class="text-muted">Learn how to use Aurex effectively</p>
                    <a href="/docs.php" class="btn btn-info">Read Docs</a>
                </div>
            </div>
        </div>
    </div>
</div>

<?php include __DIR__ . '/../templates/footer.php'; ?>
