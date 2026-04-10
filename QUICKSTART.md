# Aurex - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- 10GB disk space

### Step 1: Clone and Configure
```bash
# Clone the repository
git clone https://github.com/nkosinathil/file-comparison.git
cd file-comparison

# Create environment file
cp .env.example .env

# (Optional) Edit .env for custom configuration
# nano .env
```

### Step 2: Deploy
```bash
# Run the deployment script
sudo ./deploy.sh

# Wait for services to start (about 30 seconds)
```

### Step 3: Access
Open your browser and navigate to:
- **Web Interface**: http://localhost
- **API Documentation**: http://localhost:8000/docs

### Step 4: Login
Get your admin credentials:
```bash
# Check the password file (created on first run)
cat initial_admin_password.txt

# Or check API logs
docker-compose logs api | grep "Initial password"
```

Use these credentials to login:
- **Username**: admin
- **Password**: [from file or logs]

⚠️ **Important**: Change the password immediately after first login!

## 📋 What's Next?

### Create Your First Case
1. Click "New Case" in the dashboard
2. Enter case details (name, evidence number, investigator)
3. Select input folder with PDF bank statements
4. Choose output folder for results
5. Click "Create Case"

### Upload Bank Statements
1. Open your case
2. Click "Upload Files"
3. Select PDF bank statements (multiple files supported)
4. Wait for upload to complete

### Process Statements
1. Click "Start Processing"
2. Watch real-time progress updates
3. Processing will extract all transactions automatically

### Analyze Results
1. Once processing is complete, view insights
2. Use AI chat to query transactions
3. Explore network visualization
4. Export results as needed

## 🔧 Common Tasks

### View Logs
```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# View web logs only
docker-compose logs -f web
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Update Application
```bash
git pull origin main
sudo ./deploy.sh --pull
```

## 🛠️ Troubleshooting

### Can't Access Web Interface
```bash
# Check if containers are running
docker-compose ps

# Restart web container
docker-compose restart web

# Check web logs
docker-compose logs web
```

### API Not Responding
```bash
# Check API health
curl http://localhost:8000/api/health

# Restart API
docker-compose restart api

# Check API logs
docker-compose logs api
```

### Permission Issues
```bash
# Fix permissions
sudo chown -R $USER:$USER data logs uploads
sudo chmod -R 755 data logs uploads
```

## 🔐 Security Setup

### Change Admin Password
1. Log in with default credentials
2. Go to Profile
3. Click "Change Password"
4. Enter new secure password

### Enable SSO (Optional)
1. Edit `.env` file:
   ```env
   SSO_ENABLED=true
   SSO_PROVIDER=oauth  # or saml
   # Add your OAuth/SAML configuration
   ```
2. Restart services:
   ```bash
   docker-compose restart
   ```

### Enable HTTPS (Production)
1. Obtain SSL certificates
2. Place in `docker/nginx/ssl/`
3. Update `docker/nginx/conf.d/default.conf`
4. Uncomment SSL configuration
5. Restart nginx:
   ```bash
   docker-compose restart nginx
   ```

## 📊 Usage Tips

### Best Practices
- Organize cases by investigation
- Use descriptive case names
- Keep statements in date order
- Regular backups of data directory
- Monitor disk space usage

### File Requirements
- **Format**: PDF only
- **Size**: Up to 50MB per file
- **Naming**: Use consistent naming (e.g., accountNumber_date.pdf)
- **Quality**: Clear, readable scans

### Performance
- Process large batches overnight
- Close unused browser tabs
- Monitor system resources
- Use SSD for data storage

## 🆘 Getting Help

### Documentation
- Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- API documentation: http://localhost:8000/docs
- Application logs: `docker-compose logs`

### Common Issues
1. **Port already in use**: Change ports in docker-compose.yml
2. **Out of disk space**: Clean up old Docker images
3. **Slow processing**: Increase CPU/RAM allocation
4. **Upload fails**: Check file size limits

### Health Checks
```bash
# Check all services
docker-compose ps

# Test API
curl http://localhost:8000/api/health

# Test web
curl http://localhost
```

## 🎯 Next Steps

1. ✅ Deploy application
2. ✅ Login and change password
3. ✅ Create first case
4. ✅ Upload statements
5. ✅ Start processing
6. ✅ Analyze results

### Advanced Features
- Configure SSO authentication
- Set up automated backups
- Enable monitoring and alerts
- Scale for multiple users
- Integrate with external systems

### Production Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- SSL/TLS setup
- Performance tuning
- Security hardening
- Scaling strategies
- Monitoring setup

---

**Ready to deploy!** Run `sudo ./deploy.sh` and start analyzing! 🚀
