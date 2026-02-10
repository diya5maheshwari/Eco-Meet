import { View, Text, TouchableOpacity, StyleSheet, Animated, Easing } from "react-native";
import { useEffect, useRef } from "react";
import { router } from "expo-router";

export default function Landing() {
  const fade = useRef(new Animated.Value(0)).current;
  const slide = useRef(new Animated.Value(20)).current;
  const pulse = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fade, {
        toValue: 1,
        duration: 700,
        useNativeDriver: true,
      }),
      Animated.timing(slide, {
        toValue: 0,
        duration: 700,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1.05,
          duration: 1200,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 0.92,
          duration: 1200,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [fade, slide, pulse]);

  return (
    <View style={styles.container}>
      <View style={styles.orbOne} />
      <View style={styles.orbTwo} />

      <Animated.View
        style={[
          styles.card,
          {
            opacity: fade,
            transform: [{ translateY: slide }],
          },
        ]}
      >
        <Text style={styles.title}>VoiceAuth</Text>
        <Text style={styles.subtitle}>
          Speak. Transcribe. Save your history.
        </Text>

        <Animated.View style={[styles.micRing, { transform: [{ scale: pulse }] }]}>
          <View style={styles.micDot} />
        </Animated.View>

        <Text style={styles.body}>
          Convert speech to text on web and mobile, securely stored in your account.
        </Text>

        <TouchableOpacity
          onPress={() => router.push("/login")}
          style={styles.primaryButton}
        >
          <Text style={styles.primaryText}>Login</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/register")}
          style={styles.secondaryButton}
        >
          <Text style={styles.secondaryText}>Create Account</Text>
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0b1020",
    justifyContent: "center",
    padding: 16,
  },
  orbOne: {
    position: "absolute",
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: "#1d4ed8",
    opacity: 0.25,
    top: -40,
    right: -80,
  },
  orbTwo: {
    position: "absolute",
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: "#22d3ee",
    opacity: 0.18,
    bottom: -40,
    left: -60,
  },
  card: {
    backgroundColor: "#111827",
    borderRadius: 20,
    padding: 22,
    borderWidth: 1,
    borderColor: "#1f2937",
  },
  title: {
    color: "#f8fafc",
    fontSize: 30,
    fontWeight: "800",
    textAlign: "center",
  },
  subtitle: {
    color: "#94a3b8",
    textAlign: "center",
    marginTop: 6,
    marginBottom: 18,
  },
  micRing: {
    alignSelf: "center",
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 2,
    borderColor: "#38bdf8",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 16,
  },
  micDot: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: "#38bdf8",
  },
  body: {
    color: "#cbd5f5",
    textAlign: "center",
    marginBottom: 16,
  },
  primaryButton: {
    backgroundColor: "#2563eb",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
  primaryText: {
    color: "#f8fafc",
    fontWeight: "700",
  },
  secondaryButton: {
    marginTop: 10,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
    alignItems: "center",
  },
  secondaryText: {
    color: "#e2e8f0",
    fontWeight: "600",
  },
});
