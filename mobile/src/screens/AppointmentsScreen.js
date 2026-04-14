// Appointments Screen — Elite Salon (No Emojis, Production Clean)
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  RefreshControl, ActivityIndicator, Alert, Linking,
} from 'react-native';
import { COLORS } from '../config';
import { getAppointments, updateAppointment } from '../services/api';

const STATUS_CONFIG = {
  booked: { color: COLORS.primary, label: 'BOOKED', borderColor: COLORS.primary },
  completed: { color: COLORS.outline, label: 'COMPLETED', borderColor: COLORS.outlineVariant + '30' },
  cancelled: { color: COLORS.error, label: 'CANCELLED', borderColor: COLORS.error + '50' },
  rescheduled: { color: COLORS.secondary, label: 'RESCHEDULED', borderColor: COLORS.secondary + '50' },
};

export default function AppointmentsScreen() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedDate, setSelectedDate] = useState('today');
  const [selectedStatus, setSelectedStatus] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const filters = {};
      if (selectedDate === 'today') filters.date = new Date().toISOString().split('T')[0];
      else if (selectedDate === 'tomorrow') {
        const t = new Date(); t.setDate(t.getDate() + 1);
        filters.date = t.toISOString().split('T')[0];
      }
      if (selectedStatus) filters.status = selectedStatus;
      const result = await getAppointments(filters);
      setAppointments(result.appointments);
    } catch (e) { console.log(e.message); }
    finally { setLoading(false); setRefreshing(false); }
  }, [selectedDate, selectedStatus]);

  useEffect(() => { setLoading(true); fetchData(); }, [selectedDate, selectedStatus]);
  const onRefresh = () => { setRefreshing(true); fetchData(); };

  const handleStatusChange = (id, newStatus) => {
    Alert.alert('Confirm', `Mark as ${newStatus}?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Confirm', onPress: async () => { await updateAppointment(id, { status: newStatus }); fetchData(); } },
    ]);
  };

  const renderAppointment = ({ item }) => {
    const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.booked;
    const time = new Date(item.start_time);
    const endTime = new Date(item.end_time);
    const isBooked = item.status === 'booked';
    const isDimmed = item.status === 'completed' || item.status === 'cancelled';

    return (
      <View style={[styles.card, { borderLeftColor: config.borderColor, opacity: isDimmed ? 0.5 : 1 }]}>
        <View style={styles.cardHeader}>
          <View style={{ flex: 1 }}>
            <TouchableOpacity onPress={() => Linking.openURL(`tel:${item.customer_phone}`)}>
              <Text style={styles.cardName}>{item.customer_name}</Text>
            </TouchableOpacity>
            <Text style={styles.cardService}>{item.service.toUpperCase()}</Text>
          </View>
          <View style={styles.priceBlock}>
            <Text style={styles.cardPrice}>{'\u20B9'}{item.service_price}</Text>
            <View style={styles.statusRow}>
              <View style={[styles.statusDot, { backgroundColor: config.color }]} />
              <Text style={[styles.statusLabel, { color: config.color }]}>{config.label}</Text>
            </View>
          </View>
        </View>

        <View style={styles.metaRow}>
          <View style={styles.metaItem}>
            <View style={styles.clockIcon}>
              <View style={{ width: 8, height: 8, borderRadius: 4, borderWidth: 1, borderColor: COLORS.outline }} />
              <View style={{ width: 1, height: 3, backgroundColor: COLORS.outline, position: 'absolute', top: 2, left: 3.5 }} />
            </View>
            <Text style={styles.metaText}>
              {time.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} - {endTime.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
            </Text>
          </View>
          <View style={styles.metaItem}>
            <View style={{ width: 8, height: 8, borderRadius: 4, borderWidth: 1, borderColor: COLORS.outline }} />
            <Text style={styles.metaText}>Stylist: {item.stylist}</Text>
          </View>
        </View>

        {isBooked && (
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.completeBtn} onPress={() => handleStatusChange(item.id, 'completed')}>
              <Text style={styles.completeBtnText}>COMPLETE</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.cancelBtn} onPress={() => handleStatusChange(item.id, 'cancelled')}>
              <Text style={styles.cancelBtnText}>CANCEL</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  const Chip = ({ label, active, onPress }) => (
    <TouchableOpacity style={[styles.chip, active && styles.chipActive]} onPress={onPress}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Appointments</Text>
        <Text style={styles.countText}>{appointments.length} total</Text>
      </View>

      <View style={styles.filterRow}>
        <Chip label="TODAY" active={selectedDate === 'today'} onPress={() => setSelectedDate('today')} />
        <Chip label="TOMORROW" active={selectedDate === 'tomorrow'} onPress={() => setSelectedDate('tomorrow')} />
        <Chip label="ALL" active={selectedDate === 'all'} onPress={() => setSelectedDate('all')} />
      </View>

      <View style={styles.statusFilters}>
        {['booked', 'completed', 'cancelled'].map(s => (
          <TouchableOpacity key={s} onPress={() => setSelectedStatus(selectedStatus === s ? null : s)} style={[styles.statusFilter, selectedStatus === s && styles.statusFilterActive]}>
            <View style={[styles.statusFilterDot, { backgroundColor: STATUS_CONFIG[s].color, opacity: selectedStatus === s ? 1 : 0.3 }]} />
            <Text style={[styles.statusFilterText, selectedStatus === s && { color: STATUS_CONFIG[s].color }]}>
              {STATUS_CONFIG[s].label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={appointments}
          renderItem={renderAppointment}
          keyExtractor={(item) => item.id.toString()}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
          contentContainerStyle={{ paddingBottom: 100 }}
          ListEmptyComponent={<Text style={styles.emptyText}>No appointments found</Text>}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, paddingHorizontal: 20 },
  header: { paddingTop: 60, paddingBottom: 20 },
  title: { fontSize: 32, fontWeight: '700', color: COLORS.onSurface },
  countText: { fontSize: 11, color: COLORS.outline, letterSpacing: 1, marginTop: 4 },
  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  chip: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 24, backgroundColor: COLORS.surfaceContainerHigh, borderWidth: 1, borderColor: COLORS.outlineVariant + '15' },
  chipActive: { backgroundColor: COLORS.primaryContainer },
  chipText: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 2 },
  chipTextActive: { color: COLORS.onPrimary, fontWeight: '700' },
  statusFilters: { flexDirection: 'row', gap: 16, marginBottom: 20 },
  statusFilter: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingBottom: 4 },
  statusFilterActive: { borderBottomWidth: 2, borderBottomColor: COLORS.primary },
  statusFilterDot: { width: 8, height: 8, borderRadius: 4 },
  statusFilterText: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 1.5 },
  card: {
    backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12,
    padding: 20, marginBottom: 12, borderLeftWidth: 4,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  cardName: { fontSize: 18, fontWeight: '500', color: COLORS.onSurface },
  cardService: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginTop: 4 },
  priceBlock: { alignItems: 'flex-end' },
  cardPrice: { fontSize: 16, fontWeight: '500', color: COLORS.primary },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusLabel: { fontSize: 9, letterSpacing: 1 },
  metaRow: { flexDirection: 'row', gap: 20, marginBottom: 16 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  clockIcon: { width: 12, height: 12, justifyContent: 'center', alignItems: 'center' },
  metaText: { fontSize: 12, color: COLORS.onSurface },
  actionRow: { flexDirection: 'row', gap: 12 },
  completeBtn: { flex: 1, backgroundColor: COLORS.primaryContainer, paddingVertical: 14, borderRadius: 24, alignItems: 'center' },
  completeBtnText: { fontSize: 10, fontWeight: '700', color: COLORS.onPrimary, letterSpacing: 2 },
  cancelBtn: { paddingHorizontal: 24, paddingVertical: 14, borderRadius: 24, borderWidth: 1, borderColor: COLORS.outlineVariant + '30', alignItems: 'center' },
  cancelBtnText: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 2 },
  emptyText: { fontSize: 14, color: COLORS.outline, textAlign: 'center', marginTop: 60 },
});
