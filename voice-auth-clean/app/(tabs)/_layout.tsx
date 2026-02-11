import { Tabs, usePathname, router } from 'expo-router';
import React from 'react';
import { useEffect, useState } from 'react';
import { getStoredAuthToken } from '../../services/api';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

export default function TabLayout() {
  const colorScheme = useColorScheme();
  const pathname = usePathname();
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    const loadAuth = async () => {
      const token = await getStoredAuthToken();
      setIsAuthed(Boolean(token));
    };
    loadAuth();
  }, [pathname]);

  useEffect(() => {
    if (isAuthed) return;
    if (pathname === "/mic" || pathname === "/history") {
      router.replace("/login");
    }
  }, [isAuthed, pathname]);

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
        headerShown: false,
        tabBarButton: HapticTab,
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="house.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="mic"
        options={{
          title: 'Mic',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="mic.fill" color={color} />,
          href: isAuthed ? undefined : null,
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'History',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="clock.fill" color={color} />,
          href: isAuthed ? undefined : null,
        }}
      />
      <Tabs.Screen
        name="login"
        options={{
          title: 'Login',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="person.fill" color={color} />,
          href: isAuthed ? null : undefined,
        }}
      />
      <Tabs.Screen
        name="register"
        options={{
          title: 'Register',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="person.badge.plus" color={color} />,
          href: isAuthed ? null : undefined,
        }}
      />
    </Tabs>
  );
}
