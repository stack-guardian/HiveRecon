import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Container, Nav, Navbar, NavDropdown } from 'react-bootstrap';
import Dashboard from './pages/Dashboard';
import Scans from './pages/Scans';
import Findings from './pages/Findings';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
          <Container>
            <Navbar.Brand as={Link} to="/">
              🐝 HiveRecon
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="me-auto">
                <Nav.Link as={Link} to="/">Dashboard</Nav.Link>
                <Nav.Link as={Link} to="/scans">Scans</Nav.Link>
                <Nav.Link as={Link} to="/findings">Findings</Nav.Link>
                <Nav.Link as={Link} to="/settings">Settings</Nav.Link>
              </Nav>
              <Nav>
                <NavDropdown title="Help" id="basic-nav-dropdown">
                  <NavDropdown.Item href="#docs">Documentation</NavDropdown.Item>
                  <NavDropdown.Item href="#api">API Reference</NavDropdown.Item>
                  <NavDropdown.Divider />
                  <NavDropdown.Item href="#about">About HiveRecon</NavDropdown.Item>
                </NavDropdown>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Container fluid>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scans" element={<Scans />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}

export default App;
