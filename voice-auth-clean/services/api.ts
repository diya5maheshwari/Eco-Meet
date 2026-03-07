// Central API client for the Expo frontend (Flask-only backend mode).
import axios from "axios";
import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

const envBase = (process.env.EXPO_PUBLIC_API_URL || "").trim();

const defaultBase =
  Platform.OS === "web"
    ? "http://10.228.1.65:8000/api"
    : "http://10.228.1.65:8000/api";

export const API_BASE_URL =
  envBase || defaultBase;

const API = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach Bearer token from local storage to each request.
API.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Auto-clear token if backend says the session is unauthorized.
API.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem("token");
    }
    return Promise.reject(error);
  }
);

// Authenticate user and receive JWT.
export const loginUser = (data: any) =>
  API.post("/auth/login", data);

// Create user account.
export const registerUser = (data: any) =>
  API.post("/auth/register", data);

// Logout endpoint (server-side compatibility; client also clears token locally).
export const logoutUser = () =>
  API.post("/auth/logout");

export default API;
