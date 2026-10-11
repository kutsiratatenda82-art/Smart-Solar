import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000`;

const client = axios.create({
  baseURL: API_URL,
});

// Add a request interceptor
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
client.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Auto logout if 401 response returned from api
      localStorage.removeItem('token');
      // We don't want to force window location reload if we are handling it in context, 
      // but emitting an event or returning rejected promise is needed.
    }
    return Promise.reject(error);
  }
);

export default client;
