import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Scans
export const getScans = async (params = {}) => {
  const response = await api.get('/scans', { params });
  return response.data;
};

export const getScan = async (scanId) => {
  const response = await api.get(`/scans/${scanId}`);
  return response.data;
};

export const createScan = async (data) => {
  const response = await api.post('/scans', data);
  return response.data;
};

export const cancelScan = async (scanId) => {
  const response = await api.delete(`/scans/${scanId}`);
  return response.data;
};

// Findings
export const getFindings = async (params = {}) => {
  const response = await api.get('/findings', { params });
  return response.data;
};

export const getScanFindings = async (scanId, params = {}) => {
  const response = await api.get(`/scans/${scanId}/findings`, { params });
  return response.data;
};

// Statistics
export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

export default api;
