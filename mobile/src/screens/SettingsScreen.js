// Settings Screen — Elite Salon System Admin with Edit Modals
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Alert, ActivityIndicator, Switch, Modal, TextInput,
} from 'react-native';
import { COLORS } from '../config';
import { getServices, updateService, clearToken, wipeDatabase } from '../services/api';

export default function SettingsScreen({ onLogout }) {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editService, setEditService] = useState(null);
  const [editFields, setEditFields] = useState({});

  const fetchServices = async () => {
    try { const r = await getServices(); setServices(r.services); }
    catch (e) { console.log(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchServices(); }, []);

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Sign out of Elite Salon?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: async () => { await clearToken(); onLogout(); } },
    ]);
  };

  const handleWipeDatabase = () => {
    Alert.alert(
      '⚠ DANGER: WIPE DATABASE ⚠',
      'This will irreversibly delete ALL customer and appointment data. Are you absolutely sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'WIPE ALL DATA',
          style: 'destructive',
          onPress: async () => {
            try {
              const res = await wipeDatabase();
              Alert.alert('Success', res.message);
            } catch (e) {
              Alert.alert('Error', e.message);
            }
          }
        },
      ]
    );
  };

  const openEdit = (s) => {
    setEditService(s);
    setEditFields({ name: s.name, price: String(s.price), duration: String(s.duration), category: s.category });
  };

  const saveEdit = async () => {
    try {
      await updateService(editService.id, {
        name: editFields.name,
        price: Number(editFields.price),
        duration: Number(editFields.duration),
        category: editFields.category,
      });
      setEditService(null);
      fetchServices();
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  const toggleServiceActive = async (s) => {
    try {
      await updateService(s.id, { is_active: !s.is_active });
      fetchServices();
    } catch (e) { console.log(e); }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.labelText}>SYSTEM ADMINISTRATION</Text>
        <Text style={styles.title}>Settings</Text>
      </View>

      {/* App Info Bento */}
      <View style={styles.bentoRow}>
        <View style={styles.bentoLarge}>
          <Text style={styles.appTitle}>Elite Salon Admin</Text>
          <Text style={styles.appVersion}>SYSTEM VERSION 1.0.0</Text>
          <View style={styles.statusPill}>
            <View style={styles.statusDotGreen} />
            <Text style={styles.statusOnline}>SYSTEM ONLINE</Text>
          </View>
        </View>
        <View style={styles.bentoSmall}>
          <View style={styles.cloudIcon}>
            <View style={styles.cloudBody} />
            <View style={styles.cloudCheckmark} />
          </View>
          <Text style={styles.syncText}>Data{'\n'}Synced</Text>
        </View>
      </View>

      {/* Services Management */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>Services Management</Text>
            <Text style={styles.sectionSub}>CONFIGURE YOUR MENU OFFERINGS</Text>
          </View>
        </View>

        {loading ? (
          <ActivityIndicator color={COLORS.primary} />
        ) : (
          services.map((s) => (
            <View key={s.id} style={[styles.serviceRow, !s.is_active && { opacity: 0.45 }]}>
              <TouchableOpacity style={{ flex: 1 }} onPress={() => openEdit(s)} activeOpacity={0.7}>
                <Text style={styles.serviceName}>{s.name}</Text>
                <View style={styles.serviceMeta}>
                  <Text style={styles.serviceMetaText}>{s.duration} MIN</Text>
                  <View style={styles.metaDot} />
                  <Text style={styles.serviceMetaText}>{s.category}</Text>
                  <View style={styles.metaDot} />
                  <Text style={styles.servicePrice}>{'\u20B9'}{s.price}</Text>
                </View>
                <Text style={styles.editHint}>Tap to edit</Text>
              </TouchableOpacity>
              <Switch
                value={s.is_active}
                onValueChange={() => toggleServiceActive(s)}
                trackColor={{ false: COLORS.surfaceContainerHighest, true: COLORS.primaryContainer }}
                thumbColor="#ffffff"
              />
            </View>
          ))
        )}
      </View>

      <View style={styles.accountSection}>
        <Text style={styles.sectionTitle}>Account</Text>
        <View style={styles.accountCard}>
          <View style={styles.accountInfo}>
            <Text style={styles.accountName}>Admin</Text>
            <Text style={styles.accountRole}>ADMINISTRATOR ACCESS</Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
            <Text style={styles.logoutText}>SIGN OUT OF ELITE SALON</Text>
          </TouchableOpacity>
        </View>

        <Text style={[styles.sectionTitle, { marginTop: 28, color: COLORS.error }]}>Danger Zone</Text>
        <View style={styles.dangerCard}>
          <View style={styles.accountInfo}>
            <Text style={styles.accountName}>Factory Reset</Text>
            <Text style={styles.accountRole}>DELETE ALL CUSTOMERS & APPOINTMENTS</Text>
          </View>
          <TouchableOpacity style={styles.wipeBtn} onPress={handleWipeDatabase}>
            <Text style={styles.wipeText}>WIPE DATABASE</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={{ height: 120 }} />

      {/* Edit Service Modal */}
      <Modal visible={!!editService} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>Edit Service</Text>

            <Text style={styles.fieldLabel}>SERVICE NAME</Text>
            <TextInput
              style={styles.fieldInput}
              value={editFields.name}
              onChangeText={(v) => setEditFields(p => ({ ...p, name: v }))}
              placeholderTextColor={COLORS.outline}
            />

            <View style={styles.fieldRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.fieldLabel}>PRICE ({'\u20B9'})</Text>
                <TextInput
                  style={styles.fieldInput}
                  value={editFields.price}
                  onChangeText={(v) => setEditFields(p => ({ ...p, price: v }))}
                  keyboardType="numeric"
                  placeholderTextColor={COLORS.outline}
                />
              </View>
              <View style={{ width: 12 }} />
              <View style={{ flex: 1 }}>
                <Text style={styles.fieldLabel}>DURATION (MIN)</Text>
                <TextInput
                  style={styles.fieldInput}
                  value={editFields.duration}
                  onChangeText={(v) => setEditFields(p => ({ ...p, duration: v }))}
                  keyboardType="numeric"
                  placeholderTextColor={COLORS.outline}
                />
              </View>
            </View>

            <Text style={styles.fieldLabel}>CATEGORY</Text>
            <TextInput
              style={styles.fieldInput}
              value={editFields.category}
              onChangeText={(v) => setEditFields(p => ({ ...p, category: v }))}
              placeholderTextColor={COLORS.outline}
            />

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalCancelBtn} onPress={() => setEditService(null)}>
                <Text style={styles.modalCancelText}>CANCEL</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSaveBtn} onPress={saveEdit}>
                <Text style={styles.modalSaveText}>SAVE CHANGES</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, paddingHorizontal: 20 },
  header: { paddingTop: 60, paddingBottom: 24 },
  labelText: { fontSize: 10, color: COLORS.primary, letterSpacing: 3, marginBottom: 4 },
  title: { fontSize: 32, fontWeight: '700', color: COLORS.onSurface },
  bentoRow: { flexDirection: 'row', gap: 12, marginBottom: 28 },
  bentoLarge: { flex: 2, backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12, padding: 24 },
  appTitle: { fontSize: 20, fontWeight: '700', color: COLORS.onSurface },
  appVersion: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginTop: 4 },
  statusPill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: COLORS.surfaceContainerHigh, paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 24, alignSelf: 'flex-start', marginTop: 20,
    borderWidth: 1, borderColor: COLORS.outlineVariant + '15',
  },
  statusDotGreen: { width: 8, height: 8, borderRadius: 4, backgroundColor: COLORS.primary, shadowColor: COLORS.primary, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.6, shadowRadius: 6 },
  statusOnline: { fontSize: 9, color: COLORS.primary, letterSpacing: 1 },
  bentoSmall: { flex: 1, backgroundColor: COLORS.primary, borderRadius: 12, padding: 20, justifyContent: 'center', alignItems: 'center' },
  cloudIcon: { width: 36, height: 24, justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  cloudBody: { width: 28, height: 14, borderRadius: 7, backgroundColor: COLORS.onPrimary + '30', borderWidth: 2, borderColor: COLORS.onPrimary },
  cloudCheckmark: { width: 8, height: 4, borderBottomWidth: 2, borderLeftWidth: 2, borderColor: COLORS.onPrimary, transform: [{ rotate: '-45deg' }], position: 'absolute', bottom: 6 },
  syncText: { fontSize: 14, fontStyle: 'italic', color: COLORS.onPrimary, textAlign: 'center', lineHeight: 18 },
  section: { marginBottom: 28 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.onSurface },
  sectionSub: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginTop: 4 },
  serviceRow: {
    backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12, padding: 16,
    flexDirection: 'row', alignItems: 'center', marginBottom: 8,
  },
  serviceName: { fontSize: 16, fontWeight: '500', color: COLORS.onSurface },
  serviceMeta: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 4 },
  serviceMetaText: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 2 },
  metaDot: { width: 3, height: 3, borderRadius: 1.5, backgroundColor: COLORS.outlineVariant },
  servicePrice: { fontSize: 13, fontStyle: 'italic', fontWeight: '700', color: COLORS.primary },
  editHint: { fontSize: 9, color: COLORS.outline, marginTop: 4, letterSpacing: 0.5 },
  accountSection: { borderTopWidth: 1, borderTopColor: COLORS.outlineVariant + '15', paddingTop: 24, marginBottom: 20 },
  accountCard: { backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12, padding: 20, borderWidth: 1, borderColor: COLORS.outlineVariant + '08', marginTop: 12 },
  dangerCard: { backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12, padding: 20, borderWidth: 1, borderColor: COLORS.error + '40', marginTop: 12 },
  accountInfo: { marginBottom: 20 },
  accountName: { fontSize: 16, fontWeight: '500', color: COLORS.onSurface },
  accountRole: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginTop: 4 },
  logoutBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    padding: 16, backgroundColor: COLORS.surfaceContainerHighest, borderWidth: 1,
    borderColor: COLORS.outlineVariant + '40', borderRadius: 12,
  },
  logoutText: { fontSize: 10, fontWeight: '700', color: COLORS.onSurface, letterSpacing: 2 },
  wipeBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    padding: 16, backgroundColor: COLORS.errorContainer + '25', borderWidth: 1,
    borderColor: COLORS.errorContainer + '40', borderRadius: 12,
  },
  wipeText: { fontSize: 10, fontWeight: '700', color: COLORS.error, letterSpacing: 2 },
  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.65)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: COLORS.surfaceContainer, borderTopLeftRadius: 28, borderTopRightRadius: 28, padding: 28 },
  modalHandle: { width: 48, height: 4, backgroundColor: COLORS.outlineVariant + '40', borderRadius: 2, alignSelf: 'center', marginBottom: 20 },
  modalTitle: { fontSize: 22, fontWeight: '700', color: COLORS.onSurface, marginBottom: 24 },
  fieldLabel: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginBottom: 6 },
  fieldInput: {
    backgroundColor: COLORS.surfaceContainerLow, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 12,
    fontSize: 15, color: COLORS.onSurface, borderWidth: 1, borderColor: COLORS.outlineVariant + '20', marginBottom: 16,
  },
  fieldRow: { flexDirection: 'row' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  modalCancelBtn: { flex: 1, paddingVertical: 16, borderRadius: 24, borderWidth: 1, borderColor: COLORS.outlineVariant + '30', alignItems: 'center' },
  modalCancelText: { fontSize: 11, fontWeight: '600', color: COLORS.onSurfaceVariant, letterSpacing: 2 },
  modalSaveBtn: { flex: 1, paddingVertical: 16, borderRadius: 24, backgroundColor: COLORS.primaryContainer, alignItems: 'center' },
  modalSaveText: { fontSize: 11, fontWeight: '700', color: COLORS.onPrimary, letterSpacing: 2 },
});
