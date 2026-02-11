import axios from "axios";
import { Platform } from "react-native";
import Constants from "expo-constants";
import AsyncStorage from "@react-native-async-storage/async-storage";

const host =
  Constants.expoConfig?.hostUri?.split(":")[0] ||
  Constants.expoGoConfig?.debuggerHost?.split(":")[0];

const defaultBase =
  Platform.OS === "web"
    ? "http://localhost:5000/api"
    : host
    ? `http://${host}:5000/api`
    : "http://192.168.1.38:5000/api";

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || defaultBase;
export const API_FALLBACK_URL =
  process.env.EXPO_PUBLIC_API_URL_FALLBACK || "";

const API = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

const TOKEN_KEY = "auth_token";

export const getStoredAuthToken = async () => {
  try {
    return await AsyncStorage.getItem(TOKEN_KEY);
  } catch (e) {
    console.log("Token read error", e);
    return null;
  }
};

export const setAuthToken = async (token: string) => {
  try {
    await AsyncStorage.setItem(TOKEN_KEY, token);
  } catch (e) {
    console.log("Token save error", e);
  }
};

export const clearAuthToken = async () => {
  try {
    await AsyncStorage.removeItem(TOKEN_KEY);
  } catch (e) {
    console.log("Token clear error", e);
  }
};

API.interceptors.request.use(async (config) => {
  try {
    const token = await getStoredAuthToken();
    if (token) {
      config.headers = {
        ...(config.headers || {}),
        Authorization: `Bearer ${token}`,
      };
    }
  } catch (e) {
    console.log("Token read error", e);
  }
  return config;
});

let usingFallback = false;
const shouldFallback = (err: any) => {
  const msg = (err?.message || "").toLowerCase();
  if (msg.includes("network error")) return true;
  const data = err?.response?.data;
  if (typeof data === "string") {
    const text = data.toLowerCase();
    if (text.includes("ngrok") || text.includes("err_ngrok_3200")) return true;
  }
  return false;
};

API.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (!usingFallback && API_FALLBACK_URL && shouldFallback(err)) {
      usingFallback = true;
      API.defaults.baseURL = API_FALLBACK_URL;
      const config = {
        ...err.config,
        baseURL: API_FALLBACK_URL,
      };
      return API.request(config);
    }
    return Promise.reject(err);
  }
);

export const loginUser = (data: any) =>
  API.post("/auth/login", data);

export const registerUser = (data: any) =>
  API.post("/auth/register", data);

export const logoutUser = () =>
  API.post("/auth/logout");

export const getMe = () =>
  API.get("/auth/me");

export default API;
