// Customers Screen — Elite Salon Directory (No Emojis, Clean Icons)
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TextInput,
  TouchableOpacity, RefreshControl, ActivityIndicator, Linking, Modal, ScrollView,
} from 'react-native';
import { COLORS, FONTS, RADIUS } from '../config';
import { getCustomers, getCustomerDetail } from '../services/api';

export default function CustomersScreen() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState(null);

  const fetchData = useCallback(async () => {
    try { const r = await getCustomers(search); setCustomers(r.customers); }
    catch (e) { console.log(e.message); }
    finally { setLoading(false); setRefreshing(false); }
  }, [search]);

  useEffect(() => { const t = setTimeout(() => fetchData(), 300); return () => clearTimeout(t); }, [search]);
  useEffect(() => { fetchData(); }, []);
  const onRefresh = () => { setRefreshing(true); fetchData(); };

  const showDetail = async (id) => {
    try { const d = await getCustomerDetail(id); setSelectedCustomer(d); }
    catch (e) { console.log(e.message); }
  };

  const renderCustomer = ({ item }) => (
    <TouchableOpacity style={styles.card} onPress={() => showDetail(item.id)} activeOpacity={0.7}>
      <View style={styles.cardAvatar}>
        <Text style={styles.cardAvatarText}>{item.name.charAt(0).toUpperCase()}</Text>
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cardName}>{item.name}</Text>
        <Text style={styles.cardPhone}>{item.phone}</Text>
      </View>
      <View style={styles.cardRight}>
        <Text style={styles.visitLabel}>VISITS</Text>
        <Text style={styles.visitCount}>{item.total_visits}</Text>
      </View>
      <TouchableOpacity
        style={styles.callBtn}
        onPress={() => Linking.openURL(`tel:${item.phone}`)}
      >
        <View style={styles.callIconShape}>
          <View style={styles.callIconBar} />
          <View style={styles.callIconReceiver} />
        </View>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Directory</Text>
          <Text style={styles.countText}>{customers.length} clients</Text>
        </View>
      </View>

      <View style={styles.searchWrapper}>
        <View style={styles.searchIcon}>
          <View style={styles.searchCircle} />
          <View style={styles.searchHandle} />
        </View>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name or phone..."
          placeholderTextColor={COLORS.outline + '60'}
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={customers}
          renderItem={renderCustomer}
          keyExtractor={(item) => item.id.toString()}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
          contentContainerStyle={{ paddingBottom: 100 }}
          ListEmptyComponent={<Text style={styles.emptyText}>No customers found</Text>}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Detail Bottom Sheet Modal */}
      <Modal visible={!!selectedCustomer} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            {selectedCustomer && (
              <ScrollView showsVerticalScrollIndicator={false}>
                <View style={styles.modalProfile}>
                  <View style={styles.modalAvatarRing}>
                    <View style={styles.modalAvatar}>
                      <Text style={styles.modalAvatarText}>{selectedCustomer.name.charAt(0)}</Text>
                    </View>
                  </View>
                  <Text style={styles.modalName}>{selectedCustomer.name}</Text>
                  <View style={styles.modalMeta}>
                    <Text style={styles.modalPhone}>{selectedCustomer.phone}</Text>
                    <View style={styles.metaDot} />
                    <Text style={styles.modalTier}>{selectedCustomer.total_visits >= 10 ? 'GOLD STATUS' : 'STANDARD'}</Text>
                  </View>
                  <View style={styles.modalVisitsBlock}>
                    <Text style={styles.modalVisitsCount}>{selectedCustomer.total_visits}</Text>
                    <Text style={styles.modalVisitsLabel}>LIFETIME VISITS</Text>
                  </View>
                </View>

                <Text style={styles.historyTitle}>BOOKING HISTORY</Text>
                {selectedCustomer.appointments.length === 0 ? (
                  <Text style={styles.emptyText}>No bookings yet</Text>
                ) : (
                  selectedCustomer.appointments.slice(0, 10).map((a) => {
                    const statusColor = a.status === 'completed' ? COLORS.success : a.status === 'cancelled' ? COLORS.error : COLORS.primary;
                    return (
                      <View key={a.id} style={styles.historyItem}>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.historyService}>{a.service}</Text>
                          <Text style={styles.historyDate}>
                            {new Date(a.start_time).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })} — {a.stylist}
                          </Text>
                        </View>
                        <View style={[styles.historyBadge, { backgroundColor: statusColor + '15' }]}>
                          <Text style={[styles.historyBadgeText, { color: statusColor }]}>{a.status.toUpperCase()}</Text>
                        </View>
                      </View>
                    );
                  })
                )}

                <TouchableOpacity style={styles.closeBtn} onPress={() => setSelectedCustomer(null)}>
                  <Text style={styles.closeBtnText}>CLOSE PROFILE</Text>
                </TouchableOpacity>
                <View style={{ height: 40 }} />
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, paddingHorizontal: 20 },
  header: { paddingTop: 60, paddingBottom: 16 },
  title: { fontSize: 32, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },
  countText: { fontSize: 11, color: COLORS.outline, letterSpacing: 1, marginTop: 4, fontFamily: FONTS.body },
  searchWrapper: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'transparent', borderBottomWidth: 1, borderBottomColor: COLORS.outlineVariant, marginBottom: 16, paddingHorizontal: 14, paddingVertical: 4 },
  searchIcon: { marginRight: 10, width: 18, height: 18, justifyContent: 'center', alignItems: 'center' },
  searchCircle: { width: 12, height: 12, borderRadius: 6, borderWidth: 1.5, borderColor: COLORS.outline },
  searchHandle: { width: 1.5, height: 5, backgroundColor: COLORS.outline, position: 'absolute', bottom: 0, right: 2, transform: [{ rotate: '45deg' }] },
  searchInput: { flex: 1, paddingVertical: 14, fontSize: 14, color: COLORS.onSurface, fontFamily: FONTS.body },
  card: {
    backgroundColor: COLORS.surfaceContainerLow,
    borderRadius: RADIUS.xl,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.surfaceContainerHighest,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  cardAvatarText: { fontSize: 18, fontWeight: '600', color: COLORS.onSurface, fontFamily: FONTS.display },
  cardBody: { flex: 1 },
  cardName: { fontSize: 16, fontWeight: '600', color: COLORS.onSurface, fontFamily: FONTS.display },
  cardPhone: { fontSize: 12, color: COLORS.outline, marginTop: 2, fontFamily: FONTS.body },
  cardRight: { alignItems: 'center', marginRight: 12 },
  visitLabel: { fontSize: 8, color: COLORS.outline, letterSpacing: 2, fontFamily: FONTS.body },
  visitCount: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginTop: 2 },
  callBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.secondaryContainer,
    justifyContent: 'center',
    alignItems: 'center',
  },
  callIconShape: { width: 18, height: 18, justifyContent: 'center', alignItems: 'center' },
  callIconBar: { width: 14, height: 6, borderRadius: 3, backgroundColor: COLORS.primary, transform: [{ rotate: '-45deg' }] },
  callIconReceiver: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.primary, position: 'absolute', top: 2, left: 1 },
  emptyText: { fontSize: 14, color: COLORS.outline, textAlign: 'center', paddingVertical: 24 },
  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.65)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: COLORS.surfaceContainerLow, borderTopLeftRadius: RADIUS.xl, borderTopRightRadius: RADIUS.xl, padding: 28, maxHeight: '85%' },
  modalHandle: { width: 48, height: 4, backgroundColor: COLORS.outlineVariant + '40', borderRadius: 2, alignSelf: 'center', marginBottom: 20 },
  modalProfile: { alignItems: 'center', marginBottom: 28 },
  modalAvatarRing: { width: 80, height: 80, borderRadius: 40, padding: 3, backgroundColor: 'transparent', marginBottom: 16 },
  modalAvatar: { flex: 1, borderRadius: 37, backgroundColor: COLORS.surfaceContainerHighest, justifyContent: 'center', alignItems: 'center' },
  modalAvatarText: { fontSize: 28, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },
  modalName: { fontSize: 28, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },
  modalMeta: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 6 },
  modalPhone: { fontSize: 13, color: COLORS.outline },
  metaDot: { width: 4, height: 4, borderRadius: 2, backgroundColor: COLORS.outlineVariant },
  modalTier: { fontSize: 12, color: COLORS.primary, fontWeight: '600', letterSpacing: 0.5 },
  modalVisitsBlock: { alignItems: 'center', marginTop: 16 },
  modalVisitsCount: { fontSize: 36, fontWeight: '700', color: COLORS.primary },
  modalVisitsLabel: { fontSize: 9, color: COLORS.outline, letterSpacing: 3, marginTop: 2 },
  historyTitle: { fontSize: 11, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginBottom: 12 },
  historyItem: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.surfaceContainerHigh, borderRadius: 12, padding: 14, marginBottom: 8 },
  historyService: { fontSize: 14, fontWeight: '500', color: COLORS.onSurface },
  historyDate: { fontSize: 11, color: COLORS.outline, marginTop: 2, fontFamily: FONTS.body },
  historyBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 12 },
  historyBadgeText: { fontSize: 8, fontWeight: '600', letterSpacing: 1 },
  closeBtn: { paddingVertical: 16, borderRadius: RADIUS.xl, borderWidth: 1, borderColor: COLORS.outlineVariant, alignItems: 'center', marginTop: 20 },
  closeBtnText: { fontSize: 12, fontWeight: '600', color: COLORS.primary, letterSpacing: 2 },
});
