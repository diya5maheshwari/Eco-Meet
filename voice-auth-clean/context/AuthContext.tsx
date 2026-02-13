import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter, useSegments } from 'expo-router';

type User = {
    id: number;
    name: string;
    email: string;
    role: string;
};

type AuthContextType = {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (token: string, user: User) => Promise<void>;
    register: (token: string, user: User) => Promise<void>;
    logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
    user: null,
    token: null,
    isLoading: true,
    login: async () => { },
    register: async () => { },
    logout: async () => { },
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const segments = useSegments();

    useEffect(() => {
        const loadStorageData = async () => {
            try {
                const storedToken = await AsyncStorage.getItem('token');
                const storedUser = await AsyncStorage.getItem('user');

                if (storedToken && storedUser) {
                    setToken(storedToken);
                    setUser(JSON.parse(storedUser));
                }
            } catch (e) {
                console.error('Failed to load auth data', e);
            } finally {
                setIsLoading(false);
            }
        };

        loadStorageData();
    }, []);

    useEffect(() => {
        if (isLoading) return;

        const inAuthGroup = segments[0] === 'auth';

        if (!user && !inAuthGroup) {
            // Redirect to the sign-in page.
            router.replace('/auth/login');
        } else if (user && inAuthGroup) {
            // Redirect away from the sign-in page.
            router.replace('/(tabs)');
        }
    }, [user, segments, isLoading]);

    const login = async (newToken: string, newUser: User) => {
        setIsLoading(true);
        setToken(newToken);
        setUser(newUser);
        await AsyncStorage.setItem('token', newToken);
        await AsyncStorage.setItem('user', JSON.stringify(newUser));
        setIsLoading(false);
    };

    const register = async (newToken: string, newUser: User) => {
        setIsLoading(true);
        setToken(newToken);
        setUser(newUser);
        await AsyncStorage.setItem('token', newToken);
        await AsyncStorage.setItem('user', JSON.stringify(newUser));
        setIsLoading(false);
    };

    const logout = async () => {
        setIsLoading(true);
        setToken(null);
        setUser(null);
        await AsyncStorage.removeItem('token');
        await AsyncStorage.removeItem('user');
        setIsLoading(false);
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
