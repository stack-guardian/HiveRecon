import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Spinner, Alert, Form, Button } from 'react-bootstrap';
import api from '../api';

function Findings() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('');
  const [includeFp, setIncludeFp] = useState(false);

  useEffect(() => {
    fetchFindings();
  }, [filterSeverity, includeFp]);

  const fetchFindings = async () => {
    try {
      const data = await api.getFindings({
        severity: filterSeverity || undefined,
        include_fp: includeFp,
      });
      setFindings(data.findings || []);
      setLoading(false);
    } catch (err) {
      setError('Failed to load findings');
      setLoading(false);
    }
  };

  const getSeverityBadge = (severity) => {
    const variants = {
      critical: 'danger',
      high: 'danger',
      medium: 'warning',
      low: 'info',
      info: 'secondary',
    };
    return <Badge bg={variants[severity] || 'secondary'}>{severity.toUpperCase()}</Badge>;
  };

  const getTypeIcon = (type) => {
    const icons = {
      subdomain: '🌐',
      open_port: '🔌',
      endpoint: '🔗',
      vulnerability: '⚠️',
      mcp_analysis: '🤖',
    };
    return icons[type] || '📄';
  };

  if (loading && findings.length === 0) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading findings...</p>
      </div>
    );
  }

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <h2>🎯 Security Findings</h2>
          <p className="text-muted">Discovered assets and vulnerabilities</p>
        </Col>
      </Row>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Filters */}
      <Card className="mb-4">
        <Card.Body>
          <Row>
            <Col md={4}>
              <Form.Group>
                <Form.Label>Filter by Severity</Form.Label>
                <Form.Select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="info">Informational</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={4}>
              <Form.Group>
                <Form.Label>Options</Form.Label>
                <div className="mt-2">
                  <Form.Check
                    type="checkbox"
                    label="Include False Positives"
                    checked={includeFp}
                    onChange={(e) => setIncludeFp(e.target.checked)}
                  />
                </div>
              </Form.Group>
            </Col>
            <Col md={4} className="d-flex align-items-end">
              <Badge bg="primary" className="fs-6">
                {findings.length} Findings
              </Badge>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Findings Table */}
      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Type</th>
                <th>Severity</th>
                <th>Title</th>
                <th>Location</th>
                <th>AI Analysis</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((finding) => (
                <tr key={finding.id}>
                  <td>
                    <span className="me-2">{getTypeIcon(finding.finding_type)}</span>
                    {finding.finding_type}
                  </td>
                  <td>{getSeverityBadge(finding.severity)}</td>
                  <td>
                    <strong>{finding.title}</strong>
                    {finding.ai_analysis?.is_false_positive && (
                      <Badge bg="warning" text="dark" className="ms-2">
                        Likely FP
                      </Badge>
                    )}
                  </td>
                  <td>
                    <code className="text-truncate" style={{maxWidth: '300px', display: 'block'}}>
                      {finding.location || 'N/A'}
                    </code>
                  </td>
                  <td>
                    {finding.ai_analysis ? (
                      <Badge bg="info">
                        Analyzed
                      </Badge>
                    ) : (
                      <span className="text-muted">Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          {findings.length === 0 && !loading && (
            <div className="text-center py-5">
              <p className="text-muted">No findings match your filters.</p>
              <Button variant="outline-primary" onClick={() => {
                setFilterSeverity('');
                setIncludeFp(false);
              }}>
                Clear Filters
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>
    </Container fluid>
  );
}

export default Findings;
