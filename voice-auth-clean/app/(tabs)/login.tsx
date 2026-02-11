import { View, Text, TextInput, TouchableOpacity } from "react-native";
import { useState } from "react";
import { router } from "expo-router";

import { loginUser, setAuthToken, API_BASE_URL } from "../../services/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    if (!email || !password) {
      alert("Please enter email and password");
      return;
    }

    try {
      const res = await loginUser({ email, password });
      if (res.data?.token) {
        await setAuthToken(res.data.token);
      }
      alert("Login success");
      router.replace("/mic");
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || "Login failed";
      console.log("LOGIN ERROR", err?.response?.data || err?.message);
      if ((err?.message || "").toLowerCase().includes("network error")) {
        alert(`Cannot connect to server: ${API_BASE_URL}`);
      } else if ((msg || "").toLowerCase().includes("otp") || (msg || "").toLowerCase().includes("verify")) {
        alert("Login failed");
      } else {
        alert(msg);
      }
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Login</Text>
        <Text style={styles.subtitle}>Sign in to access your voice history</Text>

        <TextInput
          placeholder="Email"
          placeholderTextColor="#94a3b8"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          autoCapitalize="none"
          keyboardType="email-address"
        />

        <TextInput
          placeholder="Password"
          placeholderTextColor="#94a3b8"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.input}
        />

        <TouchableOpacity onPress={handleLogin} style={styles.primaryButton}>
          <Text style={styles.primaryText}>Login</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.push("/register")} style={{ marginTop: 16 }}>
          <Text style={styles.linkText}>
            Don't have an account? <Text style={styles.linkHighlight}>Register</Text>
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = {
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
    justifyContent: "center",
    padding: 16,
  },
  card: {
    backgroundColor: "#111827",
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: "#1f2937",
  },
  title: {
    color: "#f8fafc",
    fontSize: 26,
    fontWeight: "800" as const,
    textAlign: "center" as const,
  },
  subtitle: {
    color: "#94a3b8",
    textAlign: "center" as const,
    marginTop: 6,
    marginBottom: 18,
  },
  input: {
    backgroundColor: "#0b1220",
    color: "#e2e8f0",
    padding: 14,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#1f2937",
  },
  primaryButton: {
    backgroundColor: "#2563eb",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center" as const,
    marginTop: 6,
  },
  primaryText: {
    color: "#f8fafc",
    fontWeight: "700" as const,
  },
  linkText: {
    color: "#94a3b8",
    textAlign: "center" as const,
  },
  linkHighlight: {
    color: "#38bdf8",
    fontWeight: "700" as const,
  },
};
