// API service — handles all backend communication
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../config';

let authToken = null;

export async function loadToken() {
  authToken = await AsyncStorage.getItem('admin_token');
  return authToken;
}

export async function saveToken(token) {
  authToken = token;
  await AsyncStorage.setItem('admin_token', token);
}

export async function clearToken() {
  authToken = null;
  await AsyncStorage.removeItem('admin_token');
}

async function request(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });

  if (response.status === 401) {
    await clearToken();
    throw new Error('UNAUTHORIZED');
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }

  return data;
}

// Auth
export async function login(pin) {
  const data = await request('/login', {
    method: 'POST',
    body: JSON.stringify({ pin }),
  });
  if (data.token) {
    await saveToken(data.token);
  }
  return data;
}

// Dashboard
export async function getDashboard() {
  return request('/dashboard');
}

// Appointments
export async function getAppointments(filters = {}) {
  const params = new URLSearchParams();
  if (filters.date) params.append('date', filters.date);
  if (filters.status) params.append('status', filters.status);
  const qs = params.toString();
  return request(`/appointments${qs ? '?' + qs : ''}`);
}

export async function updateAppointment(id, body) {
  return request(`/appointments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

// Customers
export async function getCustomers(search = '') {
  const qs = search ? `?search=${encodeURIComponent(search)}` : '';
  return request(`/customers${qs}`);
}

export async function getCustomerDetail(id) {
  return request(`/customers/${id}`);
}

// Stylists
export async function getStylists() {
  return request('/stylists');
}

export async function updateStylist(id, body) {
  return request(`/stylists/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

// Services
export async function getServices() {
  return request('/services');
}

export async function updateService(id, body) {
  return request(`/services/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

// System
export async function wipeDatabase() {
  return request('/wipe-database', {
    method: 'DELETE',
  });
}

// Push Notifications
export async function registerDevice(expoPushToken, deviceName) {
  return request('/register-device', {
    method: 'POST',
    body: JSON.stringify({ expo_push_token: expoPushToken, device_name: deviceName }),
  });
}
