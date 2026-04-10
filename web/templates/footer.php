    </main>
    
    <!-- Footer -->
    <footer class="footer mt-auto py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">
                <?php echo APP_NAME; ?> v<?php echo APP_VERSION; ?> &copy; <?php echo date('Y'); ?>
            </span>
        </div>
    </footer>
    
    <!-- JavaScript -->
    <script src="/assets/js/bootstrap.bundle.min.js"></script>
    <script src="/assets/js/fontawesome.min.js"></script>
    <script src="/assets/js/app.js"></script>
    
    <?php if (isset($extraJS)): ?>
        <?php foreach ($extraJS as $js): ?>
            <script src="<?php echo htmlspecialchars($js); ?>"></script>
        <?php endforeach; ?>
    <?php endif; ?>
</body>
</html>
