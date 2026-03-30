import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Spinner, Alert } from 'react-bootstrap';
import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import api from '../api';

const COLORS = ['#e94560', '#fd79a8', '#fdcb6e', '#74b9ff', '#a29bfe'];

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await api.getStats();
      setStats(data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load statistics');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return <Alert variant="danger">{error}</Alert>;
  }

  const severityData = stats?.findings?.by_severity
    ? Object.entries(stats.findings.by_severity).map(([name, value]) => ({ name, value }))
    : [];

  const statusData = stats?.scans?.by_status
    ? Object.entries(stats.scans.by_status).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <h2>📊 Dashboard Overview</h2>
          <p className="text-muted">Welcome to HiveRecon - AI-Powered Reconnaissance</p>
        </Col>
        <Col xs="auto">
          <Button variant="primary" href="/scans">+ New Scan</Button>
        </Col>
      </Row>

      {/* Statistics Cards */}
      <Row>
        <Col md={3}>
          <div className="stat-card">
            <h3>{stats?.scans?.total || 0}</h3>
            <p>Total Scans</p>
          </div>
        </Col>
        <Col md={3}>
          <div className="stat-card">
            <h3>{stats?.findings?.total || 0}</h3>
            <p>Total Findings</p>
          </div>
        </Col>
        <Col md={3}>
          <div className="stat-card">
            <h3>{stats?.findings?.by_severity?.critical || 0}</h3>
            <p>Critical Findings</p>
          </div>
        </Col>
        <Col md={3}>
          <div className="stat-card">
            <h3>{stats?.scans?.by_status?.running || 0}</h3>
            <p>Active Scans</p>
          </div>
        </Col>
      </Row>

      {/* Charts */}
      <Row className="mt-4">
        <Col md={6}>
          <Card>
            <Card.Header>Findings by Severity</Card.Header>
            <Card.Body>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>Scans by Status</Card.Header>
            <Card.Body>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statusData}>
                  <XAxis dataKey="name" stroke="#aaa" />
                  <YAxis stroke="#aaa" />
                  <Tooltip />
                  <Bar dataKey="value" fill="#e94560" />
                </BarChart>
              </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Header>Quick Actions</Card.Header>
            <Card.Body>
              <Row>
                <Col md={3}>
                  <Button variant="outline-primary" className="w-100 mb-2" href="/scans">
                    View All Scans
                  </Button>
                </Col>
                <Col md={3}>
                  <Button variant="outline-success" className="w-100 mb-2" href="/findings">
                    View Findings
                  </Button>
                </Col>
                <Col md={3}>
                  <Button variant="outline-info" className="w-100 mb-2" href="/settings">
                    Settings
                  </Button>
                </Col>
                <Col md={3}>
                  <Button variant="outline-secondary" className="w-100 mb-2" href="#docs">
                    Documentation
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;
