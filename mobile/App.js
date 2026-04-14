// Salon Admin — Main App with Push Notifications
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  ActivityIndicator, Platform, Alert,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { loadToken, registerDevice } from './src/services/api';
import { COLORS } from './src/config';

import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import AppointmentsScreen from './src/screens/AppointmentsScreen';
import CustomersScreen from './src/screens/CustomersScreen';
import StylistsScreen from './src/screens/StylistsScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Configure how notifications appear when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

const TABS = [
  { key: 'dashboard', label: 'HOME' },
  { key: 'appointments', label: 'BOOKINGS' },
  { key: 'customers', label: 'CLIENTS' },
  { key: 'stylists', label: 'TEAM' },
  { key: 'settings', label: 'SETTINGS' },
];

// Icon components (CSS shapes, no emojis)
const HomeIcon = ({ color }) => (
  <View style={{ width: 20, height: 20, alignItems: 'center', justifyContent: 'flex-end' }}>
    <View style={{ width: 0, height: 0, borderLeftWidth: 10, borderRightWidth: 10, borderBottomWidth: 8, borderLeftColor: 'transparent', borderRightColor: 'transparent', borderBottomColor: color }} />
    <View style={{ width: 14, height: 10, borderWidth: 1.5, borderColor: color, borderTopWidth: 0, marginTop: -1 }} />
  </View>
);

const BookingsIcon = ({ color }) => (
  <View style={{ width: 18, height: 20, borderWidth: 1.5, borderColor: color, borderRadius: 3 }}>
    <View style={{ marginTop: 4, marginLeft: 3, gap: 3 }}>
      <View style={{ width: 10, height: 1.5, backgroundColor: color }} />
      <View style={{ width: 7, height: 1.5, backgroundColor: color }} />
      <View style={{ width: 10, height: 1.5, backgroundColor: color }} />
    </View>
  </View>
);

const ClientsIcon = ({ color }) => (
  <View style={{ width: 24, height: 20, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'center' }}>
    <View style={{ alignItems: 'center', marginRight: -4 }}>
      <View style={{ width: 8, height: 8, borderRadius: 4, borderWidth: 1.5, borderColor: color }} />
      <View style={{ width: 12, height: 6, borderTopLeftRadius: 6, borderTopRightRadius: 6, borderWidth: 1.5, borderColor: color, borderBottomWidth: 0, marginTop: 1 }} />
    </View>
    <View style={{ alignItems: 'center', marginLeft: -4 }}>
      <View style={{ width: 8, height: 8, borderRadius: 4, borderWidth: 1.5, borderColor: color }} />
      <View style={{ width: 12, height: 6, borderTopLeftRadius: 6, borderTopRightRadius: 6, borderWidth: 1.5, borderColor: color, borderBottomWidth: 0, marginTop: 1 }} />
    </View>
  </View>
);

const TeamIcon = ({ color }) => (
  <View style={{ width: 20, height: 20, justifyContent: 'center', alignItems: 'center' }}>
    <View style={{ width: 16, height: 2, backgroundColor: color, transform: [{ rotate: '-20deg' }], position: 'absolute', top: 5 }} />
    <View style={{ width: 16, height: 2, backgroundColor: color, transform: [{ rotate: '20deg' }], position: 'absolute', top: 12 }} />
    <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: color, position: 'absolute', left: 3, top: 4 }} />
  </View>
);

const SettingsIcon = ({ color }) => (
  <View style={{ width: 20, height: 20, justifyContent: 'center', alignItems: 'center' }}>
    <View style={{ width: 14, height: 14, borderRadius: 7, borderWidth: 1.5, borderColor: color }} />
    <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: color, position: 'absolute' }} />
  </View>
);

const ICONS = { dashboard: HomeIcon, appointments: BookingsIcon, customers: ClientsIcon, stylists: TeamIcon, settings: SettingsIcon };

// Register for push notifications
async function registerForPushNotifications() {
  if (!Device.isDevice) {
    console.log('Push notifications require a physical device');
    return null;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.log('Push notification permission not granted');
    return null;
  }

  // Set notification channel for Android
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('bookings', {
      name: 'Booking Alerts',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      sound: 'default',
    });
  }

  const tokenData = await Notifications.getExpoPushTokenAsync({
    projectId: undefined, // Uses the projectId from app.json automatically
  });
  return tokenData.data;
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [visitedTabs, setVisitedTabs] = useState({ dashboard: true });
  const notificationListener = useRef();
  const responseListener = useRef();

  const switchTab = useCallback((key) => {
    setActiveTab(key);
    setVisitedTabs(prev => ({ ...prev, [key]: true }));
  }, []);

  // Setup push notifications after login
  const setupPushNotifications = useCallback(async () => {
    try {
      const token = await registerForPushNotifications();
      if (token) {
        console.log('Expo Push Token:', token);
        await registerDevice(token, Device.modelName || 'Admin Device');
        console.log('Device registered for notifications');
      }
    } catch (e) {
      console.log('Push notification setup error:', e.message);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const token = await loadToken();
        if (token) {
          setIsLoggedIn(true);
        }
      } catch (e) { console.log(e); }
      finally { setChecking(false); }
    })();

    // Listen for incoming notifications while app is open
    notificationListener.current = Notifications.addNotificationReceivedListener(notification => {
      const { title, body } = notification.request.content;
      console.log('Notification received:', title, body);
    });

    // Listen for when user taps a notification
    responseListener.current = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;
      if (data?.type === 'new_booking') {
        switchTab('appointments');
      }
    });

    return () => {
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(notificationListener.current);
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
  }, []);

  // Register for push when logged in
  useEffect(() => {
    if (isLoggedIn) {
      setupPushNotifications();
    }
  }, [isLoggedIn]);

  const handleLogin = useCallback(() => {
    setIsLoggedIn(true);
  }, []);

  if (checking) {
    return (
      <View style={styles.loadingContainer}>
        <StatusBar style="light" />
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!isLoggedIn) return <LoginScreen onLogin={handleLogin} />;

  const SCREEN_MAP = { dashboard: DashboardScreen, appointments: AppointmentsScreen, customers: CustomersScreen, stylists: StylistsScreen, settings: SettingsScreen };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.screenContainer}>
        {TABS.map((tab) => {
          if (!visitedTabs[tab.key]) return null;
          const Screen = SCREEN_MAP[tab.key];
          const isActive = activeTab === tab.key;
          const extraProps = tab.key === 'settings' ? { onLogout: () => setIsLoggedIn(false) } : {};
          return (
            <View key={tab.key} style={[styles.screenContainer, { display: isActive ? 'flex' : 'none' }]}>
              <Screen {...extraProps} />
            </View>
          );
        })}
      </View>

      <View style={styles.tabBar}>
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          const color = isActive ? COLORS.navActive : COLORS.navInactive;
          const Icon = ICONS[tab.key];
          return (
            <TouchableOpacity
              key={tab.key}
              style={[styles.tab, isActive && styles.tabActive]}
              onPress={() => switchTab(tab.key)}
              activeOpacity={0.7}
            >
              <Icon color={color} />
              <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>{tab.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  loadingContainer: { flex: 1, backgroundColor: COLORS.bg, justifyContent: 'center', alignItems: 'center' },
  screenContainer: { flex: 1 },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: COLORS.navBg,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingBottom: 28,
    paddingTop: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -10 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
  },
  tab: { flex: 1, alignItems: 'center', paddingVertical: 6, gap: 4 },
  tabActive: { backgroundColor: COLORS.surfaceContainerHigh + '60', borderRadius: 12, marginHorizontal: 2 },
  tabLabel: { fontSize: 9, color: COLORS.navInactive, letterSpacing: 0.5 },
  tabLabelActive: { color: COLORS.navActive, fontWeight: '600' },
});
