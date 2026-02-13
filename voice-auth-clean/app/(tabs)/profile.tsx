import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useEffect, useState, useCallback } from 'react';
import API from '../../services/api';
import { useFocusEffect } from 'expo-router';

export default function Profile() {
    const { user, logout } = useAuth();
    const [stats, setStats] = useState({ meetings: 0, hoursSaved: 0, contacts: 0 });
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const [resMeetings, resContacts] = await Promise.all([
                API.get("/meetings/history"),
                API.get("/contacts/count")
            ]);

            const items = resMeetings.data?.items || [];
            const count = items.length;
            const contactCount = resContacts.data?.count || 0;

            setStats({
                meetings: count,
                hoursSaved: Number((count * 0.5).toFixed(1)),
                contacts: contactCount
            });
            console.log(`Synced Contacts Count: ${contactCount}`);
        } catch (e) {
            console.log("Failed to fetch stats", e);
        } finally {
            setLoading(false);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchStats();
        }, [])
    );

    return (
        <ScrollView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Profile</Text>
            </View>


            <View style={styles.profileCard}>
                <View style={styles.avatarContainer}>
                    <View style={styles.avatar}>
                        <Text style={styles.avatarText}>{user?.name?.charAt(0).toUpperCase() || 'U'}</Text>
                    </View>
                </View>
                <Text style={styles.name}>{user?.name || 'User Name'}</Text>
                <Text style={styles.email}>{user?.email || 'email@example.com'}</Text>
                <View style={styles.badge}>
                    <Text style={styles.badgeText}>Pro Member</Text>
                </View>
            </View>

            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Dashboard</Text>
                <View style={styles.statsRow}>
                    <View style={styles.statCard}>
                        <Ionicons name="calendar" size={24} color="#3b82f6" />
                        <Text style={styles.statValue}>
                            {loading ? <ActivityIndicator size="small" color="#3b82f6" /> : stats.meetings}
                        </Text>
                        <Text style={styles.statLabel}>Meetings</Text>
                    </View>
                    <View style={styles.statCard}>
                        <Ionicons name="time" size={24} color="#10b981" />
                        <Text style={styles.statValue}>
                            {loading ? <ActivityIndicator size="small" color="#10b981" /> : `${stats.hoursSaved}h`}
                        </Text>
                        <Text style={styles.statLabel}>Recorded</Text>
                    </View>
                </View>
            </View>

            <TouchableOpacity style={styles.logoutButton} onPress={logout}>
                <Text style={styles.logoutText}>Log Out</Text>
            </TouchableOpacity>

            <View style={{ height: 40 }} />
        </ScrollView >
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
    },
    header: {
        padding: 24,
        paddingTop: 60,
        backgroundColor: '#1e293b',
        borderBottomLeftRadius: 24,
        borderBottomRightRadius: 24,
        marginBottom: 20,
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: '700',
        color: '#f8fafc',
    },
    profileCard: {
        alignItems: 'center',
        marginBottom: 30,
    },
    avatarContainer: {
        marginBottom: 16,
        padding: 4,
        backgroundColor: '#1e293b',
        borderRadius: 50,
    },
    avatar: {
        width: 90,
        height: 90,
        borderRadius: 45,
        backgroundColor: '#3b82f6',
        justifyContent: 'center',
        alignItems: 'center',
    },
    avatarText: {
        fontSize: 36,
        fontWeight: 'bold',
        color: '#fff',
    },
    name: {
        fontSize: 24,
        fontWeight: '700',
        color: '#f8fafc',
        marginBottom: 4,
    },
    email: {
        fontSize: 16,
        color: '#94a3b8',
        marginBottom: 12,
    },
    badge: {
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        paddingHorizontal: 12,
        paddingVertical: 4,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: 'rgba(59, 130, 246, 0.3)',
    },
    badgeText: {
        color: '#60a5fa',
        fontSize: 12,
        fontWeight: '600',
    },
    section: {
        paddingHorizontal: 24,
        marginBottom: 24,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#e2e8f0',
        marginBottom: 16,
    },
    statsRow: {
        flexDirection: 'row',
        gap: 16,
    },
    statCard: {
        flex: 1,
        backgroundColor: '#1e293b',
        padding: 16,
        borderRadius: 16,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#334155',
    },
    statValue: {
        fontSize: 22,
        fontWeight: '700',
        color: '#f8fafc',
        marginVertical: 4,
    },
    statLabel: {
        fontSize: 14,
        color: '#94a3b8',
    },
    logoutButton: {
        marginHorizontal: 24,
        backgroundColor: 'rgba(239, 68, 68, 0.15)',
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: 'rgba(239, 68, 68, 0.3)',
    },
    logoutText: {
        color: '#f87171',
        fontSize: 16,
        fontWeight: '600',
    },
});
