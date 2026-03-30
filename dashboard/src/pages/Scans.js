import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Button, Badge, Spinner, Alert, Modal, Form } from 'react-bootstrap';
import api from '../api';

function Scans() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewScan, setShowNewScan] = useState(false);
  const [newScanData, setNewScanData] = useState({
    target: '',
    platform: '',
    program_id: '',
  });

  useEffect(() => {
    fetchScans();
    const interval = setInterval(fetchScans, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchScans = async () => {
    try {
      const data = await api.getScans();
      setScans(data.scans || []);
      setLoading(false);
    } catch (err) {
      setError('Failed to load scans');
      setLoading(false);
    }
  };

  const handleCreateScan = async () => {
    try {
      await api.createScan(newScanData);
      setShowNewScan(false);
      setNewScanData({ target: '', platform: '', program_id: '' });
      fetchScans();
    } catch (err) {
      alert('Failed to create scan: ' + err.message);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: 'secondary',
      running: 'info',
      completed: 'success',
      failed: 'danger',
      cancelled: 'warning',
    };
    return <Badge bg={variants[status] || 'secondary'}>{status}</Badge>;
  };

  if (loading && scans.length === 0) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading scans...</p>
      </div>
    );
  }

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <h2>🔍 Reconnaissance Scans</h2>
          <p className="text-muted">Manage and monitor your security scans</p>
        </Col>
        <Col xs="auto">
          <Button variant="primary" onClick={() => setShowNewScan(true)}>
            + New Scan
          </Button>
        </Col>
      </Row>

      {error && <Alert variant="danger">{error}</Alert>}

      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Scan ID</th>
                <th>Target</th>
                <th>Platform</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((scan) => (
                <tr key={scan.scan_id}>
                  <td><code>{scan.scan_id}</code></td>
                  <td>{scan.target}</td>
                  <td>{scan.platform || '-'}</td>
                  <td>{getStatusBadge(scan.status)}</td>
                  <td>{new Date(scan.created_at).toLocaleString()}</td>
                  <td>
                    <Button
                      variant="outline-sm"
                      size="sm"
                      href={`/scans/${scan.scan_id}`}
                      className="me-2"
                    >
                      View
                    </Button>
                    {scan.status === 'running' || scan.status === 'pending' ? (
                      <Button
                        variant="outline-danger"
                        size="sm"
                        onClick={() => api.cancelScan(scan.scan_id)}
                      >
                        Cancel
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          {scans.length === 0 && !loading && (
            <div className="text-center py-5">
              <p className="text-muted">No scans yet. Create your first scan!</p>
              <Button variant="primary" onClick={() => setShowNewScan(true)}>
                + New Scan
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* New Scan Modal */}
      <Modal show={showNewScan} onHide={() => setShowNewScan(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create New Scan</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Target Domain *</Form.Label>
              <Form.Control
                type="text"
                placeholder="example.com"
                value={newScanData.target}
                onChange={(e) => setNewScanData({...newScanData, target: e.target.value})}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Platform (Optional)</Form.Label>
              <Form.Select
                value={newScanData.platform}
                onChange={(e) => setNewScanData({...newScanData, platform: e.target.value})}
              >
                <option value="">Select platform</option>
                <option value="hackerone">HackerOne</option>
                <option value="bugcrowd">Bugcrowd</option>
                <option value="intigriti">Intigriti</option>
              </Form.Select>
            </Form.Group>
            {newScanData.platform && (
              <Form.Group className="mb-3">
                <Form.Label>Program ID</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="e.g., 12345"
                  value={newScanData.program_id}
                  onChange={(e) => setNewScanData({...newScanData, program_id: e.target.value})}
                />
              </Form.Group>
            )}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowNewScan(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleCreateScan}
            disabled={!newScanData.target}
          >
            Start Scan
          </Button>
        </Modal.Footer>
      </Modal>
    </Container fluid>
  );
}

export default Scans;
