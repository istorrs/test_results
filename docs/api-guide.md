# API Guide

Complete guide for using the Test Results Database API.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API supports two authentication methods:

### 1. JWT Tokens (for Web UI)

Used for user authentication in the web interface.

**Login:**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Using the token:**
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 2. API Keys (for CI/CD)

Used for automated test result submission from CI/CD pipelines.

**Using an API key:**
```bash
X-API-Key: your-api-key-here
```

## API Endpoints

### Authentication

#### Register User

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "testuser",
  "password": "securepassword123"
}
```

#### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Get Current User

```bash
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Projects

#### Create Project

```bash
POST /api/v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_name": "my-app",
  "display_name": "My Application",
  "description": "Main application test results"
}
```

#### List Projects

```bash
GET /api/v1/projects
Authorization: Bearer <token>
```

#### Get Project

```bash
GET /api/v1/projects/my-app
Authorization: Bearer <token>
```

#### Generate API Key

```bash
POST /api/v1/projects/my-app/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jenkins CI",
  "expires_days": 365
}
```

**Response:**
```json
{
  "key_id": "a1b2c3d4-...",
  "api_key": "Abc123Xyz...",
  "name": "Jenkins CI",
  "created_at": "2025-01-01T00:00:00",
  "expires_at": "2026-01-01T00:00:00"
}
```

**Important:** Save the `api_key` value! It's only shown once.

#### Revoke API Key

```bash
DELETE /api/v1/projects/my-app/api-keys/KEY_ID
Authorization: Bearer <token>
```

### Test Results

#### Submit Test Results

```bash
POST /api/v1/results
X-API-Key: <api-key>
Content-Type: multipart/form-data

junit_xml: <file>
metadata: {
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
}
```

#### List Test Results

```bash
GET /api/v1/results?project_name=my-app&branch=main&status=failure&limit=20
Authorization: Bearer <token>
```

**Query Parameters:**
- `project_name` - Filter by project
- `branch` - Filter by branch
- `status` - Filter by status (success, failure, partial)
- `start_date` - Filter by start date (ISO 8601)
- `end_date` - Filter by end date (ISO 8601)
- `tags` - Filter by tags (comma-separated)
- `page` - Page number (default: 1)
- `limit` - Results per page (default: 50)

#### Get Test Run Details

```bash
GET /api/v1/results/RUN_ID
Authorization: Bearer <token>
```

#### Get Test Case History

```bash
GET /api/v1/results/test-cases/test_login/history?project_name=my-app&limit=50
Authorization: Bearer <token>
```

#### Delete Test Run

```bash
DELETE /api/v1/results/RUN_ID
Authorization: Bearer <token>
```

## CI/CD Integration Examples

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        TEST_DB_API_KEY = credentials('test-db-api-key')
        TEST_DB_URL = 'http://testdb-server:8000'
    }

    stages {
        stage('Test') {
            steps {
                sh 'pytest --junit-xml=results.xml'
            }
        }

        stage('Upload Results') {
            steps {
                script {
                    sh """
                    curl -X POST ${TEST_DB_URL}/api/v1/results \\
                      -H "X-API-Key: ${TEST_DB_API_KEY}" \\
                      -F "junit_xml=@results.xml" \\
                      -F 'metadata={
                        "source": {
                          "type": "jenkins",
                          "job_name": "${JOB_NAME}",
                          "build_number": ${BUILD_NUMBER},
                          "branch": "${GIT_BRANCH}",
                          "commit_sha": "${GIT_COMMIT}",
                          "job_url": "${BUILD_URL}"
                        },
                        "versions": {
                          "testware_version": "v1.0.0",
                          "sut_version": "${APP_VERSION}",
                          "environment": "staging"
                        },
                        "tags": ["scheduled", "nightly"]
                      }'
                    """
                }
            }
        }
    }
}
```

### GitHub Actions

```yaml
name: Run Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: pytest --junit-xml=results.xml

    - name: Upload test results
      if: always()
      env:
        TEST_DB_API_KEY: ${{ secrets.TEST_DB_API_KEY }}
        TEST_DB_URL: ${{ secrets.TEST_DB_URL }}
      run: |
        curl -X POST $TEST_DB_URL/api/v1/results \
          -H "X-API-Key: $TEST_DB_API_KEY" \
          -F "junit_xml=@results.xml" \
          -F "metadata={
            \"source\": {
              \"type\": \"github_actions\",
              \"job_name\": \"${{ github.workflow }}\",
              \"build_number\": ${{ github.run_number }},
              \"branch\": \"${{ github.ref_name }}\",
              \"commit_sha\": \"${{ github.sha }}\",
              \"author\": \"${{ github.actor }}\",
              \"job_url\": \"${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}\"
            },
            \"versions\": {
              \"testware_version\": \"v1.0.0\",
              \"sut_version\": \"${{ github.ref_name }}\",
              \"environment\": \"ci\"
            },
            \"tags\": [\"ci\", \"automated\"]
          }"
```

### GitLab CI

```yaml
test:
  stage: test
  script:
    - pytest --junit-xml=results.xml
  after_script:
    - |
      curl -X POST $TEST_DB_URL/api/v1/results \
        -H "X-API-Key: $TEST_DB_API_KEY" \
        -F "junit_xml=@results.xml" \
        -F "metadata={
          \"source\": {
            \"type\": \"gitlab_ci\",
            \"job_name\": \"$CI_JOB_NAME\",
            \"build_number\": $CI_PIPELINE_IID,
            \"branch\": \"$CI_COMMIT_REF_NAME\",
            \"commit_sha\": \"$CI_COMMIT_SHA\",
            \"job_url\": \"$CI_JOB_URL\"
          },
          \"versions\": {
            \"testware_version\": \"v1.0.0\",
            \"sut_version\": \"$CI_COMMIT_TAG\",
            \"environment\": \"ci\"
          }
        }"
```

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid credentials)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

- Default: 100 requests per minute per API key
- Configurable in `.env` file

## Best Practices

1. **Store API keys securely** - Use CI/CD secrets management
2. **Use descriptive project names** - Makes filtering easier
3. **Tag your test runs** - Helps with organization and filtering
4. **Include version info** - Tracks which version was tested
5. **Clean up old runs** - Set retention policies
6. **Monitor API usage** - Watch for failures in CI/CD

## Interactive API Documentation

Visit the interactive Swagger UI documentation at:

```
http://localhost:8000/docs
```

This provides:
- Complete API reference
- Request/response examples
- Try-it-out functionality
- Schema documentation
