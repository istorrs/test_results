# Architecture Overview

This document describes the architecture of the Test Results Database system.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CI/CD Systems                        │
│        (Jenkins, GitHub Actions, GitLab CI)             │
└─────────────────┬───────────────────────────────────────┘
                  │ API Keys
                  │ JUnit XML + Metadata
                  │
┌─────────────────▼───────────────────────────────────────┐
│                  Load Balancer / Nginx                   │
│                   (Reverse Proxy)                        │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼───────┐   ┌───────▼───────┐
│   Frontend    │   │   Backend     │
│   (React)     │   │   (FastAPI)   │
│   Port 3000   │   │   Port 8000   │
└───────────────┘   └───────┬───────┘
                            │
                    ┌───────┴────────┐
                    │                │
            ┌───────▼──────┐  ┌──────▼──────┐
            │   MongoDB    │  │   Redis     │
            │   (Primary)  │  │   (Cache)   │
            └──────────────┘  └─────────────┘
```

## Components

### Frontend (React + TypeScript)

**Purpose:** User interface for viewing and analyzing test results

**Key Features:**
- Dashboard with test run overview
- Test result filtering and search
- Test case history viewer
- Analytics and trend visualization
- Project and API key management

**Technology Stack:**
- React 18
- TypeScript
- React Router for navigation
- Axios for API calls
- Recharts for data visualization (future)

**Deployment:**
- Development: React dev server (port 3000)
- Production: Nginx serving static build

### Backend (FastAPI)

**Purpose:** RESTful API for test result management

**Key Features:**
- JUnit XML parsing
- Test result storage and retrieval
- User authentication (JWT)
- API key management for CI/CD
- Advanced querying and filtering
- Test case history tracking

**Technology Stack:**
- FastAPI (Python 3.11+)
- Motor (Async MongoDB driver)
- Pydantic for data validation
- python-jose for JWT
- passlib for password hashing
- lxml for XML parsing

**API Structure:**
```
/api/v1/
├── auth/
│   ├── register
│   ├── login
│   └── me
├── projects/
│   ├── (list/create)
│   ├── {project_name}
│   └── {project_name}/api-keys
└── results/
    ├── (submit/list)
    ├── {run_id}
    └── test-cases/{name}/history
```

### Database (MongoDB)

**Purpose:** Flexible NoSQL storage for test results

**Collections:**

1. **users** - User accounts
   - email (unique)
   - username
   - password_hash
   - created_at
   - is_active, is_admin

2. **projects** - Project configurations
   - project_name (unique)
   - display_name
   - description
   - settings (retention, notifications)
   - api_keys[]
   - members[]

3. **test_runs** - Test execution results
   - run_id (unique, UUID)
   - source (CI/CD info)
   - versions (testware, SUT)
   - summary (stats)
   - test_suites[] (hierarchical)
   - custom_metadata
   - tags[]
   - indexed_fields

**Indexes:**
```javascript
// test_runs
{ run_id: 1 } unique
{ created_at: -1 }
{ "indexed_fields.project_name": 1, created_at: -1 }
{ "source.branch": 1, created_at: -1 }
{ "indexed_fields.status": 1 }
{ "source.commit_sha": 1 }
{ "test_suites.test_cases.name": 1 }

// projects
{ project_name: 1 } unique

// users
{ email: 1 } unique
```

### Authentication & Security

**Two-Tier Authentication:**

1. **JWT Tokens** (Web UI)
   - Short-lived access tokens (30 min)
   - Long-lived refresh tokens (7 days)
   - Bearer authentication
   - User-based permissions

2. **API Keys** (CI/CD)
   - Project-scoped keys
   - SHA-256 hashed storage
   - Optional expiration
   - Read/write permissions
   - Last-used tracking

**Security Features:**
- Password hashing with bcrypt
- CORS configuration
- Rate limiting (100 req/min)
- Input validation
- SQL injection prevention
- XSS protection

## Data Flow

### Test Result Submission

```
1. CI/CD Pipeline runs tests
   └─> Generates JUnit XML

2. Pipeline uploads to API
   └─> POST /api/v1/results
       ├─ Headers: X-API-Key
       ├─ File: junit_xml
       └─ JSON: metadata

3. Backend Processing
   ├─> Verify API key
   ├─> Parse JUnit XML
   ├─> Calculate statistics
   ├─> Generate run_id
   └─> Store in MongoDB

4. Response
   └─> Return run_id and summary
```

### Test Result Querying

```
1. User logs in
   └─> POST /api/v1/auth/login
       └─> Returns JWT tokens

2. User queries results
   └─> GET /api/v1/results?filters
       ├─ Headers: Authorization Bearer
       └─> Backend queries MongoDB

3. MongoDB aggregation
   ├─> Apply filters
   ├─> Sort by date
   ├─> Paginate
   └─> Return results

4. Frontend displays
   └─> Render in UI
```

## Scalability Considerations

### Horizontal Scaling

**Backend:**
- Stateless design allows multiple instances
- Load balancer distributes requests
- Shared MongoDB connection

**Database:**
- MongoDB replica sets for high availability
- Sharding for large datasets
- Read replicas for query performance

**Frontend:**
- CDN for static assets
- Multiple nginx instances

### Vertical Scaling

- Increase container resources (CPU/RAM)
- Optimize MongoDB queries
- Add database indexes
- Implement caching layer (Redis)

## Deployment Strategies

### Development

```yaml
docker-compose.yml:
- Hot reload enabled
- Source mounted as volumes
- Exposed ports for debugging
- No security hardening
```

### Production

```yaml
docker-compose.prod.yml:
- Optimized builds
- No source mounting
- Ports bound to localhost
- Nginx reverse proxy
- SSL/TLS termination
- Log rotation
- Health checks
- Auto-restart policies
```

## Monitoring & Observability

### Logging

**Application Logs:**
- Backend: Uvicorn access logs
- Frontend: Nginx access logs
- MongoDB: Database logs

**Log Aggregation:**
- JSON format for parsing
- Structured logging
- Centralized collection (future: ELK stack)

### Health Checks

**Endpoints:**
- `GET /health` - API health
- `GET /` - Service availability

**Metrics to Track:**
- API response times
- Database query performance
- Error rates
- Upload success rates
- Storage usage

### Alerting

**Future Implementation:**
- Failed test run notifications
- API downtime alerts
- High error rate warnings
- Storage threshold alerts

## Data Retention

**Configurable per Project:**
- Default: 90 days
- Automatic cleanup of old runs
- Option to archive important runs
- Backup before deletion

**Implementation:**
```python
# Scheduled job (cron)
async def cleanup_old_runs():
    for project in projects:
        retention_days = project.settings.retention_days
        cutoff_date = now() - timedelta(days=retention_days)
        await db.test_runs.delete_many({
            "project_name": project.name,
            "created_at": {"$lt": cutoff_date}
        })
```

## Future Enhancements

### Phase 2
- Full React UI implementation
- Real-time test result updates (WebSockets)
- Advanced analytics dashboard
- Test comparison tools

### Phase 3
- Flaky test detection
- Email/Slack notifications
- Custom report generation
- Performance benchmarking

### Phase 4
- Machine learning for failure prediction
- Test execution trends
- Cost optimization recommendations
- Multi-tenancy support

## Technology Choices Rationale

### Why FastAPI?
- Async support for high performance
- Automatic OpenAPI documentation
- Type safety with Pydantic
- Modern Python features
- Easy to test and maintain

### Why MongoDB?
- Flexible schema for evolving metadata
- Excellent for hierarchical data (test suites)
- Powerful query capabilities
- Horizontal scaling support
- JSON-like documents match API structure

### Why React?
- Component-based architecture
- Large ecosystem
- TypeScript support
- Good performance
- Wide adoption

### Why Docker?
- Consistent environments
- Easy deployment
- Isolation
- Resource management
- Cloud-ready

## Performance Characteristics

### Expected Throughput

- **Test Result Uploads:** 100-500 per minute
- **API Queries:** 1000-5000 per minute
- **Concurrent Users:** 100-500
- **Database Size:** 1GB-100GB typical

### Optimization Strategies

1. **Database Indexes:** Properly indexed queries
2. **Pagination:** Limit result set sizes
3. **Caching:** Redis for frequent queries
4. **CDN:** Static asset delivery
5. **Connection Pooling:** Reuse database connections
6. **Async I/O:** Non-blocking operations

## Disaster Recovery

### Backup Strategy

**Database:**
- Daily automated backups
- Point-in-time recovery
- Off-site backup storage

**Configuration:**
- Version controlled (.env templates)
- Infrastructure as Code (docker-compose)

### Recovery Procedures

1. **Database Restore:** From latest backup
2. **Application Redeploy:** From git repository
3. **Configuration Restore:** From version control
4. **Verification:** Health checks and smoke tests

## Security Architecture

### Defense in Depth

1. **Network Layer:** Firewall, closed ports
2. **Transport Layer:** HTTPS/TLS
3. **Application Layer:** Authentication, authorization
4. **Data Layer:** Encryption at rest (MongoDB)

### Compliance Considerations

- GDPR: User data deletion support
- Audit logging: Track all modifications
- Access control: Role-based permissions
- Data retention: Configurable policies

## Conclusion

This architecture provides:
- ✅ Scalable and maintainable design
- ✅ Secure authentication for users and CI/CD
- ✅ Flexible data model for evolving needs
- ✅ Cloud-ready deployment
- ✅ Local Ubuntu server support
- ✅ Comprehensive API for integration
- ✅ Future-proof extensibility
