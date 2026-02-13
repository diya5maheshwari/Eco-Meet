// Meeting history screen backed by Flask /api/meetings/history.
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from "react-native";
import { useEffect, useState } from "react";
import API from "../../services/api";
import { useAuth } from "../../context/AuthContext";

type Item = {
  id: number;
  created_at: string;
  date: string;
  time: string;
  platform: string;
  participants: string[];
  reminder_time?: string | null;
};

export default function History() {
  // Fetch and display past meetings for the logged-in user.
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const { logout } = useAuth();

  const loadTexts = async () => {
    // Load meeting history from Flask API.
    try {
      setLoading(true);
      const res = await API.get("/meetings/history");
      setItems(res.data?.items || []);
    } catch (err) {
      console.log("History error", err);
      alert("Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial history fetch when screen mounts.
    loadTexts();
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Previous Meetings</Text>
        <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
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
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ paddingBottom: 24 }}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.text}>
              {item.date} at {item.time}
            </Text>
            <Text style={styles.time}>Platform: {item.platform}</Text>
            <Text style={styles.time}>
              Participants: {item.participants?.length ? item.participants.join(", ") : "None"}
            </Text>
            {item.reminder_time ? (
              <Text style={styles.time}>Reminder: {item.reminder_time}</Text>
            ) : null}
            <Text style={styles.time}>
              Created: {new Date(item.created_at).toLocaleString()}
            </Text>
          </View>
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>No meetings yet</Text>
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
