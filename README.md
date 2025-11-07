# Test Results Database

A comprehensive test results management system for storing, analyzing, and visualizing JUnit test reports from CI/CD pipelines (Jenkins, GitHub Actions, etc.).

## Features

- 📊 Store and manage JUnit XML test reports
- 🔍 Advanced filtering and search capabilities
- 📈 Test analytics and trend visualization
- 🔐 Secure API with JWT and API key authentication
- 🏷️ Flexible metadata and tagging system
- 📱 Modern React-based UI
- 🐳 Docker-based deployment (local and cloud-ready)
- 🔄 Support for Jenkins, GitHub Actions, and other CI/CD systems

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React 18 + TypeScript
- **Database**: MongoDB 7.0
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/istorrs/test_results.git
cd test_results

# Copy environment file and configure
cp .env.example .env
# Edit .env and set a secure SECRET_KEY

# Start all services
docker-compose up -d

# Access the application
# API Documentation: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Ubuntu Server Deployment

For production deployment on Ubuntu server, see [docs/ubuntu-deployment.md](docs/ubuntu-deployment.md)

## API Usage

### Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Create a Project

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-app",
    "display_name": "My Application",
    "description": "Main application test results"
  }'
```

### Generate API Key for CI/CD

```bash
curl -X POST http://localhost:8000/api/v1/projects/PROJECT_ID/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jenkins CI",
    "expires_days": 365
  }'
```

### Submit Test Results from Jenkins

```bash
curl -X POST http://localhost:8000/api/v1/results \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "junit_xml=@test-results.xml" \
  -F 'metadata={
    "source": {
      "type": "jenkins",
      "job_name": "my-app-tests",
      "build_number": 123,
      "branch": "main",
      "commit_sha": "abc123def456"
    },
    "versions": {
      "testware_version": "v2.3.1",
      "sut_version": "v1.5.0",
      "environment": "staging"
    },
    "tags": ["nightly", "regression"]
  }'
```

### Query Test Results

```bash
curl -X GET "http://localhost:8000/api/v1/results?project_name=my-app&branch=main&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## CI/CD Integration

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh 'pytest --junit-xml=results.xml'
            }
        }
        stage('Upload Results') {
            steps {
                script {
                    sh '''
                    curl -X POST http://testdb-server:8000/api/v1/results \
                      -H "X-API-Key: ${TEST_DB_API_KEY}" \
                      -F "junit_xml=@results.xml" \
                      -F "metadata={
                        \\"source\\": {
                          \\"type\\": \\"jenkins\\",
                          \\"job_name\\": \\"${JOB_NAME}\\",
                          \\"build_number\\": ${BUILD_NUMBER},
                          \\"branch\\": \\"${GIT_BRANCH}\\",
                          \\"commit_sha\\": \\"${GIT_COMMIT}\\"
                        },
                        \\"versions\\": {
                          \\"testware_version\\": \\"v1.0.0\\",
                          \\"sut_version\\": \\"${APP_VERSION}\\"
                        }
                      }"
                    '''
                }
            }
        }
    }
}
```

### GitHub Actions

```yaml
- name: Run Tests
  run: pytest --junit-xml=results.xml

- name: Upload Results
  env:
    TEST_DB_API_KEY: ${{ secrets.TEST_DB_API_KEY }}
  run: |
    curl -X POST http://testdb-server:8000/api/v1/results \
      -H "X-API-Key: $TEST_DB_API_KEY" \
      -F "junit_xml=@results.xml" \
      -F "metadata={
        \"source\": {
          \"type\": \"github_actions\",
          \"job_name\": \"${{ github.workflow }}\",
          \"build_number\": ${{ github.run_number }},
          \"branch\": \"${{ github.ref_name }}\",
          \"commit_sha\": \"${{ github.sha }}\"
        }
      }"
```

## Database Schema

### Test Runs Collection

```javascript
{
  _id: ObjectId,
  run_id: String,  // UUID
  created_at: ISODate,
  source: {
    type: String,  // "jenkins" | "github_actions"
    job_name: String,
    build_number: Number,
    branch: String,
    commit_sha: String
  },
  versions: {
    testware_version: String,
    sut_version: String,
    environment: String
  },
  summary: {
    total_tests: Number,
    passed: Number,
    failed: Number,
    skipped: Number,
    success_rate: Number
  },
  test_suites: [...],
  custom_metadata: Map,
  tags: [String]
}
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT)
- `POST /api/v1/auth/refresh` - Refresh JWT token

### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project details
- `POST /api/v1/projects/{id}/api-keys` - Generate API key

### Test Results
- `POST /api/v1/results` - Submit test results
- `GET /api/v1/results` - List/search test results
- `GET /api/v1/results/{run_id}` - Get specific run details
- `GET /api/v1/results/test-cases/{name}/history` - Test case history

## Documentation

- [Ubuntu Deployment Guide](docs/ubuntu-deployment.md)
- [API Guide](docs/api-guide.md)
- [Architecture Overview](docs/architecture.md)

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Security

- JWT tokens for user authentication
- API keys with project-level permissions
- HTTPS recommended for production
- Rate limiting enabled
- Input validation on all endpoints

## Future Enhancements

- Advanced analytics dashboard
- Flaky test detection
- Email/Slack notifications
- Test comparison tools
- Performance benchmarking
- Custom report generation
- Export to PDF/CSV

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions, please open a GitHub issue.
