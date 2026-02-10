import axios from "axios";
import { Platform } from "react-native";

const defaultBase =
  Platform.OS === "web"
    ? "http://localhost:5000/api"
    : "http://192.168.31.58:5000/api";

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || defaultBase;

const API = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

export const loginUser = (data: any) =>
  API.post("/auth/login", data);

export const registerUser = (data: any) =>
  API.post("/auth/register", data);

export const logoutUser = () =>
  API.post("/auth/logout");

export default API;
