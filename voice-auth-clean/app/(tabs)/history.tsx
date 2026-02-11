import { View, Text, StyleSheet, FlatList, TouchableOpacity } from "react-native";
import { useEffect, useState } from "react";
import API, {
  logoutUser,
  getMe,
  clearAuthToken,
  getStoredAuthToken,
} from "../../services/api";
import { router } from "expo-router";
import { colors } from "../../styles/theme";

type Item = {
  _id: string;
  text: string;
  createdAt: string;
};

export default function History() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  const loadTexts = async () => {
    try {
      setLoading(true);
      const res = await API.get("/user/texts");
      setItems(res.data?.items || []);
    } catch (err) {
      console.log("History error", err);
      alert("Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const checkAuthAndLoad = async () => {
      try {
        const token = await getStoredAuthToken();
        if (!token) {
          setAuthChecked(false);
          router.replace("/login");
          return;
        }
        await getMe();
        setAuthChecked(true);
        await loadTexts();
      } catch (e) {
        router.replace("/login");
      }
    };
    checkAuthAndLoad();
  }, []);

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch (e) {
      console.log("Logout error", e);
    } finally {
      await clearAuthToken();
      router.replace("/login");
    }
  };

  if (!authChecked) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Checking session...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Previous Chats</Text>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.refresh} onPress={loadTexts}>
        <Text style={styles.refreshText}>
          {loading ? "Loading..." : "Refresh"}
        </Text>
      </TouchableOpacity>

      <FlatList
        data={items}
        keyExtractor={(item) => item._id}
        contentContainerStyle={{ paddingBottom: 24 }}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.text}>{item.text}</Text>
            <Text style={styles.time}>
              {new Date(item.createdAt).toLocaleString()}
            </Text>
          </View>
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>No history yet</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
    padding: 16,
  },
  title: {
    color: "#f8fafc",
    fontSize: 22,
    fontWeight: "700",
    textAlign: "center",
    marginBottom: 12,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  refresh: {
    alignSelf: "center",
    marginBottom: 12,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: "#2563eb",
  },
  refreshText: {
    color: "#f8fafc",
    fontWeight: "600",
  },
  card: {
    backgroundColor: "#111827",
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#1f2937",
  },
  text: {
    color: "#e2e8f0",
    fontSize: 16,
    marginBottom: 6,
  },
  time: {
    color: "#94a3b8",
    fontSize: 12,
  },
  empty: {
    color: "#94a3b8",
    textAlign: "center",
    marginTop: 30,
  },
  logoutBtn: {
    backgroundColor: "#1f2937",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  logoutText: {
    color: "#e2e8f0",
    fontWeight: "600",
    fontSize: 12,
  },
});
