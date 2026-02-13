import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
  ScrollView,
  TextInput,
} from "react-native";
import { useEffect, useRef, useState } from "react";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system";
import API from "../../services/api";
import { router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";

const DEEPGRAM_API_KEY = "de69095600f4ca89395490564246f23ebdb257c6";

export default function Mic() {
  const [messages, setMessages] = useState<
    { sender: "user" | "bot"; text: string }[]
  >([]);
  const [inputText, setInputText] = useState("");
  const [listening, setListening] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);

  const recognitionRef = useRef<any>(null);
  const scrollRef = useRef<ScrollView>(null);

  // ---------------- WEB SPEECH ----------------
  useEffect(() => {
    if (Platform.OS === "web") {
      const w = typeof window !== "undefined" ? (window as any) : null;
      const SpeechRecognition =
        w?.SpeechRecognition || w?.webkitSpeechRecognition;

      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = "en-IN";
        recognition.interimResults = false;

        recognition.onresult = async (event: any) => {
          const transcript =
            event.results?.[0]?.[0]?.transcript ||
            event?.results?.[0]?.transcript ||
            "";

          if (transcript) {
            await sendToChat(transcript);
          }
        };

        recognitionRef.current = recognition;
      }
    }
  }, []);

  // ---------------- START LISTENING ----------------
  const startListening = async () => {
    if (Platform.OS === "web") {
      recognitionRef.current?.start();
      setListening(true);
      return;
    }

    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== "granted") {
        alert("Microphone permission required");
        return;
      }

      const rec = new Audio.Recording();
      await rec.prepareToRecordAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      await rec.startAsync();

      setRecording(rec);
      setListening(true);
    } catch (error) {
      console.log("Start error", error);
    }
  };

  // ---------------- STOP LISTENING ----------------
  const stopListening = async () => {
    if (Platform.OS === "web") {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    if (!recording) return;

    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      setListening(false);

      if (uri) {
        await transcribeWithDeepgram(uri);
      }
    } catch (error) {
      console.log("Stop error", error);
    }
  };

  // ---------------- DEEPGRAM ----------------
  const transcribeWithDeepgram = async (uri: string) => {
    try {
      const base64Audio = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      const response = await fetch(
        "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true",
        {
          method: "POST",
          headers: {
            Authorization: `Token ${DEEPGRAM_API_KEY}`,
            "Content-Type": "audio/m4a",
          },
          body: base64Audio,
        }
      );

      const result = await response.json();
      const transcript =
        result?.results?.channels?.[0]?.alternatives?.[0]?.transcript;

      if (transcript) {
        await sendToChat(transcript);
      }
    } catch (error) {
      console.log("Deepgram error", error);
    }
  };

  // ---------------- SEND TO BACKEND ----------------
  const sendToChat = async (messageText: string) => {
    if (!messageText.trim()) return;

    try {
      const token = await AsyncStorage.getItem("token");

      // Add user message
      setMessages((prev) => [
        ...prev,
        { sender: "user", text: messageText },
      ]);

      setInputText("");

      const res = await API.post(
        "/chat",
        { text: messageText },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.data?.length > 0) {
        const botReply = res.data[0]?.text;
        if (botReply) {
          setMessages((prev) => [
            ...prev,
            { sender: "bot", text: botReply },
          ]);
        }
      }

      setTimeout(() => {
        scrollRef.current?.scrollToEnd({ animated: true });
      }, 200);

    } catch (error: any) {
      console.log("Chat error", error.response?.data);
    }
  };

  // ---------------- LOGOUT ----------------
  const handleLogout = async () => {
    await AsyncStorage.removeItem("token");
    router.replace("/login");
  };

  // ---------------- UI ----------------
  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.title}>Speech Chat</Text>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
            <Text style={styles.logoutText}>Logout</Text>
          </TouchableOpacity>
        </View>

        <ScrollView ref={scrollRef} style={styles.box}>
          {messages.length === 0 ? (
            <Text style={styles.placeholder}>
              Start speaking or type a message...
            </Text>
          ) : (
            messages.map((msg, index) => (
              <Text
                key={index}
                style={[
                  styles.message,
                  {
                    color:
                      msg.sender === "user"
                        ? "#38bdf8"
                        : "#22c55e",
                  },
                ]}
              >
                {msg.sender === "user" ? "You: " : "Bot: "}
                {msg.text}
              </Text>
            ))
          )}
        </ScrollView>

        {/* -------- INPUT + SEND BUTTON -------- */}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Type message..."
            placeholderTextColor="#94a3b8"
            value={inputText}
            onChangeText={setInputText}
          />

          <TouchableOpacity
            style={styles.sendButton}
            onPress={() => sendToChat(inputText)}
          >
            <Text style={styles.sendText}>Send</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          onPress={listening ? stopListening : startListening}
          style={[
            styles.micButton,
            { backgroundColor: listening ? "#ef4444" : "#111827" },
          ]}
        >
          <Text style={styles.micText}>
            {listening ? "Stop" : "Start Speaking"}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ---------------- STYLES ----------------
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
    justifyContent: "center",
    padding: 16,
  },
  card: {
    backgroundColor: "#111827",
    borderRadius: 16,
    padding: 18,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  title: {
    color: "#f8fafc",
    fontSize: 20,
    fontWeight: "700",
  },
  box: {
    minHeight: 200,
    maxHeight: 350,
    borderWidth: 1,
    borderColor: "#334155",
    backgroundColor: "#0b1220",
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
  },
  message: {
    marginBottom: 8,
  },
  placeholder: {
    color: "#94a3b8",
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  input: {
    flex: 1,
    backgroundColor: "#0b1220",
    color: "#e2e8f0",
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
    marginRight: 8,
  },
  sendButton: {
    backgroundColor: "#2563eb",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  sendText: {
    color: "#fff",
    fontWeight: "600",
  },
  micButton: {
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
  },
  micText: {
    color: "#f8fafc",
    fontWeight: "700",
  },
  logoutBtn: {
    backgroundColor: "#1f2937",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  logoutText: {
    color: "#e2e8f0",
    fontSize: 12,
  },
});
