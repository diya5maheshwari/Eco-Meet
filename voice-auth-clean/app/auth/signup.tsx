import { View, Text, TextInput, TouchableOpacity } from "react-native";
import { useState } from "react";
import { useRouter } from "expo-router";

import { registerUser } from "../../services/api";
import { colors } from "../../styles/theme";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const router = useRouter();

  const handleRegister = async () => {
    if (!name || !email || !password) {
      alert("Please fill all fields");
      return;
    }

    try {
      await registerUser({ name, email, password });
      alert("Registered successfully. Please login.");
      router.replace("/auth/login");
    } catch (error: any) {
      console.log(error.response?.data);
      alert(error.response?.data?.message || "Register failed");
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Register</Text>
        <Text style={styles.subtitle}>
          Create your account to save your voice history
        </Text>

        <TextInput
          placeholder="Full Name"
          placeholderTextColor="#94a3b8"
          value={name}
          onChangeText={setName}
          style={styles.input}
        />

        <TextInput
          placeholder="Email"
          placeholderTextColor="#94a3b8"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
        />

        <TextInput
          placeholder="Password"
          placeholderTextColor="#94a3b8"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.input}
        />

        <TouchableOpacity onPress={handleRegister} style={styles.primaryButton}>
          <Text style={styles.primaryText}>Create Account</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/auth/login")}
          style={{ marginTop: 16 }}
        >
          <Text style={styles.linkText}>
            Already have an account?{" "}
            <Text style={styles.linkHighlight}>Login</Text>
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
