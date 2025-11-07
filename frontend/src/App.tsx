import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Test Results Database</h1>
        <p>Frontend MVP - Coming Soon</p>

        <div style={{ marginTop: '2rem', textAlign: 'left', maxWidth: '600px' }}>
          <h2>Backend API is Ready!</h2>
          <p>The backend API is fully functional. Access the API documentation at:</p>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: '#61dafb', fontSize: '1.2rem' }}
          >
            http://localhost:8000/docs
          </a>

          <h3 style={{ marginTop: '2rem' }}>Available Endpoints:</h3>
          <ul style={{ fontSize: '0.9rem' }}>
            <li><strong>POST /api/v1/auth/register</strong> - Register user</li>
            <li><strong>POST /api/v1/auth/login</strong> - Login</li>
            <li><strong>POST /api/v1/projects</strong> - Create project</li>
            <li><strong>POST /api/v1/projects/PROJECT/api-keys</strong> - Generate API key</li>
            <li><strong>POST /api/v1/results</strong> - Submit test results</li>
            <li><strong>GET /api/v1/results</strong> - List test results</li>
            <li><strong>GET /api/v1/results/RUN_ID</strong> - Get test run details</li>
            <li><strong>GET /api/v1/results/test-cases/NAME/history</strong> - Test case history</li>
          </ul>

          <h3 style={{ marginTop: '2rem' }}>Quick Start:</h3>
          <ol style={{ fontSize: '0.9rem', textAlign: 'left' }}>
            <li>Register a user at <code>/api/v1/auth/register</code></li>
            <li>Login to get JWT token</li>
            <li>Create a project</li>
            <li>Generate API key for CI/CD</li>
            <li>Submit test results from Jenkins/GitHub Actions</li>
          </ol>

          <p style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#1a1a1a', borderRadius: '8px' }}>
            <strong>Next Steps:</strong> Implement full React UI with test result visualization,
            filtering, analytics, and project management dashboard.
          </p>
        </div>
      </header>
    </div>
  );
}

export default App;
