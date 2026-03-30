import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Badge } from 'react-bootstrap';

function Settings() {
  const [settings, setSettings] = useState({
    ai_model: 'qwen2.5:7b',
    max_concurrent_agents: 3,
    rate_limit_enabled: true,
    requests_per_second: 10,
    audit_logging: true,
    disclaimer_required: true,
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // In a real app, this would save to backend
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <h2>⚙️ Settings</h2>
          <p className="text-muted">Configure HiveRecon behavior</p>
        </Col>
      </Row>

      {saved && <Alert variant="success">Settings saved successfully!</Alert>}

      <Row>
        <Col md={8}>
          {/* AI Settings */}
          <Card className="mb-4">
            <Card.Header>🤖 AI Configuration</Card.Header>
            <Card.Body>
              <Form.Group className="mb-3">
                <Form.Label>AI Model</Form.Label>
                <Form.Select
                  value={settings.ai_model}
                  onChange={(e) => setSettings({...settings, ai_model: e.target.value})}
                >
                  <option value="qwen2.5:7b">Qwen 2.5 7B (Recommended)</option>
                  <option value="qwen2.5:14b">Qwen 2.5 14B</option>
                  <option value="llama3">Llama 3 8B</option>
                  <option value="llama3:70b">Llama 3 70B</option>
                  <option value="mistral">Mistral 7B</option>
                  <option value="codellama">Code Llama</option>
                </Form.Select>
                <Form.Text className="text-muted">
                  Select the Ollama model for AI coordination and analysis
                </Form.Text>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Ollama Base URL</Form.Label>
                <Form.Control
                  type="text"
                  defaultValue="http://localhost:11434"
                />
              </Form.Group>
            </Card.Body>
          </Card>

          {/* Scan Settings */}
          <Card className="mb-4">
            <Card.Header>🔍 Scan Configuration</Card.Header>
            <Card.Body>
              <Form.Group className="mb-3">
                <Form.Label>Max Concurrent Agents</Form.Label>
                <Form.Control
                  type="number"
                  value={settings.max_concurrent_agents}
                  onChange={(e) => setSettings({...settings, max_concurrent_agents: parseInt(e.target.value)})}
                  min={1}
                  max={10}
                />
                <Form.Text className="text-muted">
                  Number of recon agents to run simultaneously (1-10)
                </Form.Text>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Check
                  type="checkbox"
                  label="Enable Rate Limiting"
                  checked={settings.rate_limit_enabled}
                  onChange={(e) => setSettings({...settings, rate_limit_enabled: e.target.checked})}
                />
              </Form.Group>

              {settings.rate_limit_enabled && (
                <Form.Group className="mb-3">
                  <Form.Label>Requests Per Second</Form.Label>
                  <Form.Control
                    type="number"
                    value={settings.requests_per_second}
                    onChange={(e) => setSettings({...settings, requests_per_second: parseInt(e.target.value)})}
                    min={1}
                    max={100}
                  />
                </Form.Group>
              )}
            </Card.Body>
          </Card>

          {/* Legal & Compliance */}
          <Card className="mb-4">
            <Card.Header>⚖️ Legal & Compliance</Card.Header>
            <Card.Body>
              <Form.Group className="mb-3">
                <Form.Check
                  type="checkbox"
                  label="Require Legal Disclaimer Acknowledgment"
                  checked={settings.disclaimer_required}
                  onChange={(e) => setSettings({...settings, disclaimer_required: e.target.checked})}
                />
                <Form.Text className="text-muted">
                  Users must acknowledge legal terms before scanning
                </Form.Text>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Check
                  type="checkbox"
                  label="Enable Audit Logging"
                  checked={settings.audit_logging}
                  onChange={(e) => setSettings({...settings, audit_logging: e.target.checked})}
                />
                <Form.Text className="text-muted">
                  Log all actions for accountability and compliance
                </Form.Text>
              </Form.Group>
            </Card.Body>
          </Card>

          <Button variant="primary" onClick={handleSave}>
            Save Settings
          </Button>
        </Col>

        {/* Sidebar */}
        <Col md={4}>
          <Card className="mb-4">
            <Card.Header>📊 System Status</Card.Header>
            <Card.Body>
              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>Ollama Connection</span>
                  <Badge bg="success">Connected</Badge>
                </div>
              </div>
              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>Database</span>
                  <Badge bg="success">OK</Badge>
                </div>
              </div>
              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>API Server</span>
                  <Badge bg="success">Running</Badge>
                </div>
              </div>
            </Card.Body>
          </Card>

          <Card className="mb-4">
            <Card.Header>🛠️ Installed Tools</Card.Header>
            <Card.Body>
              <div className="mb-2">
                <Badge bg="secondary" className="me-1">subfinder</Badge>
                <Badge bg="success">✓</Badge>
              </div>
              <div className="mb-2">
                <Badge bg="secondary" className="me-1">amass</Badge>
                <Badge bg="success">✓</Badge>
              </div>
              <div className="mb-2">
                <Badge bg="secondary" className="me-1">nmap</Badge>
                <Badge bg="success">✓</Badge>
              </div>
              <div className="mb-2">
                <Badge bg="secondary" className="me-1">katana</Badge>
                <Badge bg="success">✓</Badge>
              </div>
              <div className="mb-2">
                <Badge bg="secondary" className="me-1">ffuf</Badge>
                <Badge bg="success">✓</Badge>
              </div>
              <div className="mb-2">
                <Badge bg="secondary" className="me-1">nuclei</Badge>
                <Badge bg="success">✓</Badge>
              </div>
            </Card.Body>
          </Card>

          <Card>
            <Card.Header>⚠️ Important</Card.Header>
            <Card.Body>
              <p className="text-muted small">
                Always ensure you have explicit authorization before scanning any target.
                Unauthorized scanning is illegal and violates the terms of use.
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container fluid>
  );
}

export default Settings;
