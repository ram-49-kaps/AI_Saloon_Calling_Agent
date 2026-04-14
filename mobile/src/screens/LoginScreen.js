// Login Screen — Elite Salon Editorial PIN Pad
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Vibration,
  Animated, Dimensions,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { COLORS } from '../config';
import { login } from '../services/api';

const { width } = Dimensions.get('window');

export default function LoginScreen({ onLogin }) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const shakeAnim = new Animated.Value(0);

  const shake = () => {
    Animated.sequence([
      Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue: -10, duration: 50, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue: 0, duration: 50, useNativeDriver: true }),
    ]).start();
  };

  const handlePress = async (digit) => {
    if (pin.length >= 4) return;
    Vibration.vibrate(30);
    const newPin = pin + digit;
    setPin(newPin);
    setError('');

    if (newPin.length === 4) {
      setLoading(true);
      try {
        await login(newPin);
        onLogin();
      } catch (e) {
        shake();
        Vibration.vibrate(200);
        setError('Invalid PIN');
        setPin('');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleDelete = () => {
    setPin(pin.slice(0, -1));
    setError('');
  };

  const handleClear = () => {
    setPin('');
    setError('');
  };

  const renderDots = () => (
    <Animated.View style={[styles.dotsRow, { transform: [{ translateX: shakeAnim }] }]}>
      {[0, 1, 2, 3].map((i) => (
        <View
          key={i}
          style={[
            styles.dot,
            pin.length > i && styles.dotFilled,
          ]}
        />
      ))}
    </Animated.View>
  );

  const renderKey = (digit) => (
    <TouchableOpacity
      key={digit}
      style={styles.key}
      onPress={() => handlePress(digit)}
      activeOpacity={0.6}
    >
      <Text style={styles.keyText}>{digit}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Brand */}
      <View style={styles.brand}>
        <Text style={styles.brandName}>ELITE SALON</Text>
        <Text style={styles.brandSub}>MANAGEMENT SUITE</Text>
      </View>

      {/* Title */}
      <View style={styles.header}>
        <Text style={styles.title}>Enter Admin PIN</Text>
        <Text style={styles.subtitle}>SECURE ACCESS REQUIRED</Text>
      </View>

      {renderDots()}
      {error ? <Text style={styles.error}>{error}</Text> : <View style={{ height: 20 }} />}

      {/* Keypad */}
      <View style={styles.keypad}>
        <View style={styles.keyRow}>
          {['1', '2', '3'].map(renderKey)}
        </View>
        <View style={styles.keyRow}>
          {['4', '5', '6'].map(renderKey)}
        </View>
        <View style={styles.keyRow}>
          {['7', '8', '9'].map(renderKey)}
        </View>
        <View style={styles.keyRow}>
          <TouchableOpacity style={styles.keyAction} onPress={handleClear} activeOpacity={0.6}>
            <Text style={styles.keyActionText}>CLEAR</Text>
          </TouchableOpacity>
          {renderKey('0')}
          <TouchableOpacity style={styles.keyAction} onPress={handleDelete} activeOpacity={0.6}>
            <Text style={styles.keyActionText}>DEL</Text>
          </TouchableOpacity>
        </View>
      </View>

      {loading && <Text style={styles.loadingText}>Verifying...</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  brand: { alignItems: 'center', marginBottom: 48 },
  brandName: {
    fontSize: 32,
    fontStyle: 'italic',
    fontWeight: '700',
    color: COLORS.primary,
    letterSpacing: -0.5,
  },
  brandSub: {
    fontSize: 10,
    color: COLORS.outline,
    letterSpacing: 4,
    marginTop: 4,
  },
  header: { alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.onSurface },
  subtitle: {
    fontSize: 10,
    color: COLORS.outline,
    letterSpacing: 3,
    marginTop: 6,
  },
  dotsRow: { flexDirection: 'row', gap: 24, marginBottom: 8 },
  dot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    backgroundColor: COLORS.surfaceContainerLow,
  },
  dotFilled: {
    backgroundColor: COLORS.primaryContainer,
    borderColor: COLORS.primary,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 8,
  },
  error: { color: COLORS.error, fontSize: 12, height: 20, marginTop: 4, letterSpacing: 1 },
  keypad: { width: width * 0.72, marginTop: 24 },
  keyRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 16 },
  key: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.surfaceContainerLow,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.outlineVariant + '15',
  },
  keyText: { fontSize: 24, fontWeight: '300', color: COLORS.onSurface },
  keyAction: {
    width: 72,
    height: 72,
    borderRadius: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
  keyActionText: { fontSize: 10, color: COLORS.outline, letterSpacing: 2 },
  loadingText: { color: COLORS.primary, marginTop: 20, fontSize: 12, letterSpacing: 1 },
});
