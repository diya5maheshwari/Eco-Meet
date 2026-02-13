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
import * as FileSystem from "expo-file-system/legacy";
import * as Contacts from "expo-contacts";
import API from "../../services/api";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useAuth } from "../../context/AuthContext";

const DEEPGRAM_API_KEY = "de69095600f4ca89395490564246f23ebdb257c6";

type Message = {
  id: string;
  sender: "user" | "bot";
  text: string;
};

export default function Mic() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [listening, setListening] = useState(false);

  // Refs
  const recordingRef = useRef<Audio.Recording | null>(null);
  const lastSpeakingTimeRef = useRef<number>(0);
  const recognitionRef = useRef<any>(null);
  const scrollRef = useRef<ScrollView>(null);
  const isStoppingRef = useRef(false);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  // ---------------- CONTACT SYNC (Restored) ----------------
  useEffect(() => {
    (async () => {
      try {
        const { status } = await Contacts.requestPermissionsAsync();
        if (status === "granted") {
          const { data } = await Contacts.getContactsAsync({
            fields: [Contacts.Fields.Emails, Contacts.Fields.PhoneNumbers],
          });

          if (data.length > 0) {
            const formatted = data.map(c => ({
              name: c.name || "Unknown",
              phone_numbers: c.phoneNumbers?.map(p => p.number).join(",") || "",
              emails: c.emails?.map(e => e.email).join(",") || ""
            }));

            await API.post("/contacts/sync", { contacts: formatted });
          }
        } else {
          // alert("Permission to access contacts was denied");
        }
      } catch (e) {
        console.log("Contact sync failed", e);
      }
    })();
  }, []);


  // ---------------- RECORDING OPTIONS ----------------
  const recordingOptions: any = {
    android: {
      extension: ".m4a",
      outputFormat: Audio.AndroidOutputFormat.MPEG_4,
      audioEncoder: Audio.AndroidAudioEncoder.AAC,
      sampleRate: 44100,
      numberOfChannels: 1,
      bitRate: 128000,
      meteringIntervalMillis: 200,
    },
    ios: {
      extension: ".m4a",
      audioQuality: Audio.IOSAudioQuality.HIGH,
      sampleRate: 44100,
      numberOfChannels: 1,
      bitRate: 128000,
      linearPCMBitDepth: 16,
      linearPCMIsBigEndian: false,
      linearPCMIsFloat: false,
      meteringIntervalMillis: 200,
    },
    web: { mimeType: "audio/webm", bitsPerSecond: 128000 },
  };

  // ---------------- LISTEN LOGIC ----------------
  const startListening = async () => {
    if (Platform.OS === "web") {
      recognitionRef.current?.start();
      setListening(true);
      return;
    }

    try {
      if (recordingRef.current) await stopListening();

      const { status } = await Audio.requestPermissionsAsync();
      if (status !== "granted") {
        alert("Microphone permission required");
        return;
      }

      const rec = new Audio.Recording();
      await rec.prepareToRecordAsync(recordingOptions);
      rec.setProgressUpdateInterval(200);

      lastSpeakingTimeRef.current = Date.now();
      isStoppingRef.current = false;

      rec.setOnRecordingStatusUpdate((status) => {
        if (!status.isRecording || isStoppingRef.current) return;

        if (status.metering !== undefined) {
          // EXTREMELY STRICT THRESHOLD: -10dB
          // Normal speaking: -2 to -8dB
          // Silence/Noise: -40 to -160dB
          if (status.metering > -20) {
            lastSpeakingTimeRef.current = Date.now();
          } else {
            const silenceDuration = Date.now() - lastSpeakingTimeRef.current;
            if (silenceDuration > 3000) {
              console.log("Auto-stopping (3s silence)");
              stopListening();
            }
          }
        }
      });

      await rec.startAsync();
      recordingRef.current = rec;
      setListening(true);
    } catch (error) {
      console.log("Start error", error);
    }
  };

  const stopListening = async () => {
    if (Platform.OS === "web") {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    if (isStoppingRef.current) return;
    isStoppingRef.current = true;

    const rec = recordingRef.current;
    if (!rec) return;

    try {
      if (rec._canRecord) await rec.stopAndUnloadAsync();
      const uri = rec.getURI();
      recordingRef.current = null;
      setListening(false);

      if (uri) await transcribeWithDeepgram(uri);
    } catch (error) {
      console.log("Stop video error", error);
    } finally {
      isStoppingRef.current = false;
    }
  };

  // ---------------- TRANSCRIPTION ----------------
  const transcribeWithDeepgram = async (uri: string) => {
    try {
      const response = await FileSystem.uploadAsync(
        "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true",
        uri,
        {
          headers: {
            Authorization: `Token ${DEEPGRAM_API_KEY}`,
            "Content-Type": "audio/m4a",
          },
          httpMethod: "POST",
          uploadType: 0,
        }
      );

      if (response.status === 200) {
        const result = JSON.parse(response.body);
        const transcript = result?.results?.channels?.[0]?.alternatives?.[0]?.transcript;
        if (transcript) await sendToChat(transcript);
      }
    } catch (error) {
      console.log("Deepgram error", error);
    }
  };

  // ---------------- SEND TO CHAT (WITH AUTO-DELETE) ----------------
  const sendToChat = async (messageText: string) => {
    if (!messageText.trim()) return;

    try {
      const token = await AsyncStorage.getItem("token");
      const msgId = Date.now().toString();

      // 1. Add User Message
      const newUserMsg: Message = { id: msgId, sender: "user", text: messageText };
      setMessages((prev) => [...prev, newUserMsg]);
      setInputText("");

      // Auto-delete user message after 2 minutes (120000 ms)
      setTimeout(() => {
        setMessages(prev => prev.filter(m => m.id !== msgId));
      }, 120000);

      // 2. Send to Backend
      const res = await API.post(
        "/chat",
        { text: messageText },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // 3. Handle Bot Reply
      if (res.data?.length > 0) {
        const botReplyText = res.data[0]?.text;
        if (botReplyText) {
          const botMsgId = (Date.now() + 1).toString();
          const newBotMsg: Message = { id: botMsgId, sender: "bot", text: botReplyText };

          setMessages((prev) => [...prev, newBotMsg]);

          // Auto-delete bot message after 1.5 minutes
          setTimeout(() => {
            setMessages(prev => prev.filter(m => m.id !== botMsgId));
          }, 90000);
        }
      }

    } catch (error: any) {
      console.log("Chat error", error);
    }
  };

  // ---------------- RENDER ----------------
  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.title}>Welcome, {user?.name}</Text>
        </View>

        <ScrollView ref={scrollRef} style={styles.box}>
          {messages.length === 0 ? (
            <Text style={styles.placeholder}>
              Start speaking...
            </Text>
          ) : (
            messages.map((msg) => (
              <Text
                key={msg.id}
                style={[
                  styles.message,
                  { color: msg.sender === "user" ? "#38bdf8" : "#22c55e" },
                ]}
              >
                {msg.sender === "user" ? "You: " : "Bot: "}
                {msg.text}
              </Text>
            ))
          )}
        </ScrollView>

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
    flex: 1,
  },
  header: {
    flexDirection: "row",
    justifyContent: "center",
    marginBottom: 10,
  },
  title: {
    color: "#f8fafc",
    fontSize: 20,
    fontWeight: "700",
  },
  box: {
    flex: 1,
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
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
    marginRight: 8,
  },
  sendButton: {
    backgroundColor: "#2563eb",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 10,
  },
  sendText: {
    color: "#fff",
    fontWeight: "600",
  },
  micButton: {
    paddingVertical: 16,
    borderRadius: 999,
    alignItems: "center",
    backgroundColor: "#111827",
    borderWidth: 1,
    borderColor: "#334155",
  },
  micText: {
    color: "#f8fafc",
    fontWeight: "700",
  },
});
