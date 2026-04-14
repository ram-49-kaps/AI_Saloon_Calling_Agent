// Stylists Screen — Elite Salon Team (No Emojis, Edit Modal)
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, Switch,
  RefreshControl, ActivityIndicator, Linking, TouchableOpacity,
  Modal, TextInput, Alert,
} from 'react-native';
import { COLORS, FONTS, RADIUS } from '../config';
import { getStylists, updateStylist } from '../services/api';

export default function StylistsScreen() {
  const [stylists, setStylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [editStylist, setEditStylist] = useState(null);
  const [editFields, setEditFields] = useState({});

  const fetchData = useCallback(async () => {
    try { const r = await getStylists(); setStylists(r.stylists); }
    catch (e) { console.log(e.message); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { fetchData(); }, []);
  const onRefresh = () => { setRefreshing(true); fetchData(); };

  const toggleActive = async (id, val) => {
    await updateStylist(id, { is_active: !val });
    setStylists(prev => prev.map(s => s.id === id ? { ...s, is_active: !val } : s));
  };

  const openEdit = (s) => {
    setEditStylist(s);
    setEditFields({ name: s.name, phone: s.phone, specializations: s.specializations.join(', ') });
  };

  const saveEdit = async () => {
    try {
      const specs = editFields.specializations.split(',').map(s => s.trim()).filter(Boolean);
      await updateStylist(editStylist.id, {
        name: editFields.name,
        phone: editFields.phone,
        specializations: specs,
      });
      setEditStylist(null);
      fetchData();
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  const renderStylist = ({ item }) => (
    <View style={[styles.card, !item.is_active && styles.cardInactive]}>
      <View style={styles.cardTop}>
        <TouchableOpacity style={styles.avatarSection} onPress={() => openEdit(item)} activeOpacity={0.7}>
          <View style={[styles.avatarRing, !item.is_active && { opacity: 0.5 }]}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{item.name.charAt(0)}</Text>
            </View>
          </View>
          <View>
            <Text style={styles.cardName}>{item.name}</Text>
            <TouchableOpacity onPress={() => Linking.openURL(`tel:${item.phone}`)}>
              <Text style={styles.cardPhone}>{item.phone}</Text>
            </TouchableOpacity>
            <Text style={styles.editHint}>Tap avatar to edit</Text>
          </View>
        </TouchableOpacity>
        <Switch
          value={item.is_active}
          onValueChange={() => toggleActive(item.id, item.is_active)}
          trackColor={{ false: COLORS.surfaceContainerHighest, true: COLORS.primaryContainer }}
          thumbColor="#ffffff"
        />
      </View>

      <View style={styles.tagRow}>
        {item.specializations.map(spec => (
          <View key={spec} style={styles.tag}>
            <Text style={styles.tagText}>{spec.toUpperCase()}</Text>
          </View>
        ))}
      </View>

      <View style={styles.loadBar}>
        <View>
          <Text style={styles.loadLabel}>{item.is_active ? "TODAY'S LOAD" : 'STATUS'}</Text>
          <Text style={[styles.loadValue, !item.is_active && { color: COLORS.outline }]}>
            {item.is_active ? `${item.today_bookings} Bookings Today` : 'Off Duty'}
          </Text>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.labelText}>CURATION TEAM</Text>
        <Text style={styles.title}>Artisans & Stylists</Text>
        <Text style={styles.countText}>
          {stylists.filter(s => s.is_active).length} / {stylists.length} Active
        </Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={stylists}
          renderItem={renderStylist}
          keyExtractor={(item) => item.id.toString()}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
          contentContainerStyle={{ paddingBottom: 100 }}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Edit Stylist Modal */}
      <Modal visible={!!editStylist} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>Edit Stylist</Text>

            <Text style={styles.fieldLabel}>STYLIST NAME</Text>
            <TextInput
              style={styles.fieldInput}
              value={editFields.name}
              onChangeText={(v) => setEditFields(p => ({ ...p, name: v }))}
              placeholderTextColor={COLORS.outline}
            />

            <Text style={styles.fieldLabel}>PHONE NUMBER</Text>
            <TextInput
              style={styles.fieldInput}
              value={editFields.phone}
              onChangeText={(v) => setEditFields(p => ({ ...p, phone: v }))}
              keyboardType="phone-pad"
              placeholderTextColor={COLORS.outline}
            />

            <Text style={styles.fieldLabel}>SPECIALIZATIONS (comma separated)</Text>
            <TextInput
              style={styles.fieldInput}
              value={editFields.specializations}
              onChangeText={(v) => setEditFields(p => ({ ...p, specializations: v }))}
              placeholder="Hair, Facial, Nails"
              placeholderTextColor={COLORS.outline}
            />

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalCancelBtn} onPress={() => setEditStylist(null)}>
                <Text style={styles.modalCancelText}>CANCEL</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSaveBtn} onPress={saveEdit}>
                <Text style={styles.modalSaveText}>SAVE CHANGES</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, paddingHorizontal: 20 },
  header: { paddingTop: 60, paddingBottom: 20 },
  labelText: { fontSize: 10, color: COLORS.primary, letterSpacing: 3, marginBottom: 4 },
  title: { fontSize: 28, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },
  countText: { fontSize: 11, color: COLORS.outline, letterSpacing: 1, marginTop: 4, fontFamily: FONTS.body },
  card: { backgroundColor: COLORS.surfaceContainerLow, borderRadius: RADIUS.lg, padding: 20, marginBottom: 14 },
  cardInactive: { opacity: 0.45 },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 },
  avatarSection: { flexDirection: 'row', gap: 14, alignItems: 'center', flex: 1 },
  avatarRing: { width: 56, height: 56, borderRadius: 12, padding: 3, overflow: 'hidden', backgroundColor: 'transparent' },
  avatar: { flex: 1, borderRadius: 9, backgroundColor: COLORS.surfaceContainerHighest, justifyContent: 'center', alignItems: 'center' },
  avatarText: { fontSize: 20, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },
  cardName: { fontSize: 18, fontWeight: '500', color: COLORS.onSurface, fontFamily: FONTS.display },
  cardPhone: { fontSize: 13, color: COLORS.primary, marginTop: 4, fontFamily: FONTS.body },
  editHint: { fontSize: 9, color: COLORS.outline, marginTop: 2, letterSpacing: 0.5, fontFamily: FONTS.body },
  tagRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap', marginBottom: 16 },
  tag: { backgroundColor: COLORS.surfaceContainerHighest, paddingHorizontal: 14, paddingVertical: 6, borderRadius: 24 },
  tagText: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 2 },
  loadBar: { backgroundColor: COLORS.surfaceContainerHigh, borderRadius: 12, padding: 16 },
  loadLabel: { fontSize: 9, color: COLORS.outline, letterSpacing: 1 },
  loadValue: { fontSize: 18, fontWeight: '500', color: COLORS.primary, marginTop: 2 },
  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.65)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: COLORS.surfaceContainer, borderTopLeftRadius: RADIUS.xl, borderTopRightRadius: RADIUS.xl, padding: 28 },
  modalHandle: { width: 48, height: 4, backgroundColor: COLORS.outlineVariant + '40', borderRadius: 2, alignSelf: 'center', marginBottom: 20 },
  modalTitle: { fontSize: 22, fontWeight: '700', color: COLORS.onSurface, marginBottom: 24, fontFamily: FONTS.display },
  fieldLabel: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginBottom: 6, fontFamily: FONTS.body },
  fieldInput: {
    backgroundColor: 'transparent', paddingVertical: 12,
    fontSize: 15, color: COLORS.onSurface, borderBottomWidth: 1, borderBottomColor: COLORS.outlineVariant, marginBottom: 16, fontFamily: FONTS.body,
  },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  modalCancelBtn: { flex: 1, paddingVertical: 16, borderRadius: RADIUS.xl, borderWidth: 1, borderColor: COLORS.outlineVariant + '30', alignItems: 'center' },
  modalCancelText: { fontSize: 11, fontWeight: '600', color: COLORS.onSurfaceVariant, letterSpacing: 2 },
  modalSaveBtn: { flex: 1, paddingVertical: 16, borderRadius: RADIUS.xl, backgroundColor: COLORS.primaryContainer, alignItems: 'center' },
  modalSaveText: { fontSize: 11, fontWeight: '700', color: COLORS.onPrimary, letterSpacing: 2 },
});
