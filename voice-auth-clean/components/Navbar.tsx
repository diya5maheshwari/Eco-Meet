import { View, Text, TouchableOpacity } from "react-native";
import { router } from "expo-router";
import { colors } from "../styles/theme";

export default function Navbar() {
  return (
    <View
      style={{
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        paddingHorizontal: 20,
        paddingVertical: 15,
        backgroundColor: colors.card,
      }}
    >
      {/* Logo */}
      <Text style={{ color: colors.text, fontSize: 20, fontWeight: "700" }}>
        VoiceApp
      </Text>

      {/* Links */}
      <View style={{ flexDirection: "row", gap: 15 }}>
        <TouchableOpacity onPress={() => router.push("/")}>
          <Text style={{ color: colors.text }}>Home</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.push("/login")}>
          <Text style={{ color: colors.text }}>Login</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.push("/register")}>
          <Text style={{ color: colors.primary }}>Register</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
