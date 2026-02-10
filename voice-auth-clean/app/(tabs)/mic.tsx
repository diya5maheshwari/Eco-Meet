import { View, Text, TouchableOpacity, StyleSheet, Platform } from "react-native";
import { useEffect, useRef, useState } from "react";
import { Audio } from "expo-av";
import API, { API_BASE_URL, logoutUser } from "../../services/api";
import { router } from "expo-router";

export default function Mic() {
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const recognitionRef = useRef<any>(null);
  const isRecognizingRef = useRef(false);

  useEffect(() => {
    if (Platform.OS === "web") {
      const w = typeof window !== "undefined" ? (window as any) : null;
      const SpeechRecognition =
        w?.SpeechRecognition || w?.webkitSpeechRecognition;

      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = "en-IN";
        recognition.interimResults = false;
        recognition.onstart = () => {
          isRecognizingRef.current = true;
        };
        recognition.onresult = (event: any) => {
          const transcript =
            event.results?.[0]?.[0]?.transcript ||
            event?.results?.[0]?.transcript ||
            "";
          if (transcript) {
            setText(transcript);
            saveText(transcript);
          }
        };
        recognition.onerror = (e: any) => {
          console.log("Web speech error 👉", e);
          setListening(false);
          isRecognizingRef.current = false;
        };
        recognition.onend = () => {
          setListening(false);
          isRecognizingRef.current = false;
        };
        recognitionRef.current = recognition;
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop?.();
      }
    };
  }, []);

  const startListening = async () => {
    if (Platform.OS === "web") {
      if (!recognitionRef.current) {
        alert("Web Speech API not supported in this browser");
        return;
      }
      if (isRecognizingRef.current || listening) {
        return;
      }
      setText("");
      setListening(true);
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.log("Web speech start error 👉", e);
        setListening(false);
        isRecognizingRef.current = false;
      }
      return;
    }

    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== "granted") {
        alert("Microphone permission is required");
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const rec = new Audio.Recording();
      await rec.prepareToRecordAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      await rec.startAsync();
      setRecording(rec);
      setListening(true);
      setText("");
    } catch (e) {
      console.log("Start error", e);
      setListening(false);
    }
  };

  const stopListening = async () => {
    if (Platform.OS === "web") {
      recognitionRef.current?.stop?.();
      isRecognizingRef.current = false;
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
        await transcribeAudio(uri);
      }
    } catch (e) {
      console.log("Stop error", e);
      setListening(false);
    }
  };

  const getMimeType = (uri: string) => {
    const lower = uri.toLowerCase();
    if (lower.endsWith(".m4a")) return "audio/m4a";
    if (lower.endsWith(".mp3")) return "audio/mpeg";
    if (lower.endsWith(".wav")) return "audio/wav";
    if (lower.endsWith(".3gp")) return "audio/3gpp";
    return "application/octet-stream";
  };

  const transcribeAudio = async (uri: string) => {
    try {
      const mimeType = getMimeType(uri);
      const ext = uri.split(".").pop() || "m4a";
      const form = new FormData();
      form.append(
        "file",
        {
          uri,
          name: `speech.${ext}`,
          type: mimeType,
        } as any
      );

      const res = await fetch(`${API_BASE_URL}/speech/transcribe`, {
        method: "POST",
        body: form,
        credentials: "include",
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.message || "Transcription failed");
      }

      if (data?.text) {
        setText(data.text);
        saveText(data.text);
      } else {
        alert("No speech detected");
      }
    } catch (err) {
      console.log("Transcribe error", err);
      alert("Transcription failed");
    }
  };

  const saveText = async (spokenText: string) => {
    try {
      await API.post("/user/save-text", {
        text: spokenText,
      });
    } catch (err) {
      console.log("Save text error", err);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch (e) {
      console.log("Logout error", e);
    } finally {
      router.replace("/login");
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.title}>Speech to Text</Text>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
            <Text style={styles.logoutText}>Logout</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.subtitle}>
          Tap the mic, speak clearly, and your words will appear below.
        </Text>

        <View style={styles.box}>
          <Text style={styles.boxText}>{text || "Press button and speak"}</Text>
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

        <TouchableOpacity
          onPress={() => router.push("/history")}
          style={styles.secondaryButton}
        >
          <Text style={styles.secondaryText}>Previous Chats</Text>
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
    borderWidth: 1,
    borderColor: "#1f2937",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    color: "#f8fafc",
    fontSize: 22,
    fontWeight: "700",
    textAlign: "center",
  },
  subtitle: {
    color: "#94a3b8",
    textAlign: "center",
    marginTop: 6,
    marginBottom: 16,
  },
  box: {
    minHeight: 110,
    borderWidth: 1,
    borderColor: "#334155",
    backgroundColor: "#0b1220",
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  boxText: {
    color: "#e2e8f0",
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
  secondaryButton: {
    marginTop: 12,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
    alignItems: "center",
  },
  secondaryText: {
    color: "#e2e8f0",
    fontWeight: "600",
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
