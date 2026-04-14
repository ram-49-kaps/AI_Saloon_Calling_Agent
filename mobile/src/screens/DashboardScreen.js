// Dashboard Screen — Elite Salon (No Emojis, Clean Production UI)
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, RefreshControl,
  Dimensions, ActivityIndicator,
} from 'react-native';
import { BarChart, LineChart } from 'react-native-chart-kit';
import { COLORS } from '../config';
import { getDashboard } from '../services/api';

const { width } = Dimensions.get('window');
const chartWidth = width - 64;

export default function DashboardScreen() {
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try { const result = await getDashboard(); setData(result); }
    catch (e) { console.log('Dashboard error:', e.message); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const onRefresh = () => { setRefreshing(true); fetchData(); };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!data) return null;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  const chartConfig = {
    backgroundColor: COLORS.surfaceContainerLow,
    backgroundGradientFrom: COLORS.surfaceContainerLow,
    backgroundGradientTo: COLORS.surfaceContainer,
    decimalCount: 0,
    color: (opacity = 1) => `rgba(242, 202, 80, ${opacity})`,
    labelColor: () => COLORS.outline,
    propsForDots: { r: '4', strokeWidth: '2', stroke: COLORS.primaryContainer },
    propsForBackgroundLines: { strokeDasharray: '', stroke: COLORS.outlineVariant + '20' },
    barPercentage: 0.6,
  };

  const weeklyLabels = data.weekly_bookings.map(d => d.day);
  const weeklyBookingCounts = data.weekly_bookings.map(d => d.count);
  const weeklyRevenues = data.weekly_revenue.map(d => d.revenue);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero Greeting */}
      <View style={styles.header}>
        <Text style={styles.greeting}>{greeting}</Text>
        <Text style={styles.dateText}>
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()}
        </Text>
      </View>

      {/* Stats Bento Grid */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <View style={styles.statIconRow}>
            <View style={styles.statIconBox}>
              <View style={{ width: 12, height: 14, borderWidth: 1.5, borderColor: COLORS.primary, borderRadius: 2 }}>
                <View style={{ width: 6, height: 1.5, backgroundColor: COLORS.primary, marginTop: 3, marginLeft: 2 }} />
              </View>
            </View>
          </View>
          <Text style={styles.statNumber}>{String(data.today.total_bookings).padStart(2, '0')}</Text>
          <Text style={styles.statLabel}>TODAY'S BOOKINGS</Text>
        </View>
        <View style={styles.statCard}>
          <View style={styles.statIconRow}>
            <View style={styles.statIconBox}>
              <Text style={{ fontSize: 14, color: COLORS.primary, fontWeight: '700' }}>{'\u20B9'}</Text>
            </View>
          </View>
          <Text style={[styles.statNumber, { color: COLORS.primary }]}>
            {'\u20B9'}{data.today.revenue.toLocaleString()}
          </Text>
          <Text style={styles.statLabel}>TODAY'S REVENUE</Text>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <View style={styles.statIconRow}>
            <View style={styles.statIconBox}>
              <View style={{ width: 10, height: 10, borderRadius: 5, borderWidth: 1.5, borderColor: COLORS.primary }} />
            </View>
            <Text style={styles.statBadge}>{data.today.booked} Active</Text>
          </View>
          <Text style={styles.statNumber}>{String(data.today.booked).padStart(2, '0')}</Text>
          <Text style={styles.statLabel}>APPOINTMENTS LEFT</Text>
        </View>
        <View style={styles.statCard}>
          <View style={styles.statIconRow}>
            <View style={styles.statIconBox}>
              <View style={{ flexDirection: 'row', gap: 2 }}>
                <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1, borderColor: COLORS.primary }} />
                <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1, borderColor: COLORS.primary }} />
              </View>
            </View>
          </View>
          <Text style={styles.statNumber}>{data.total_customers.toLocaleString()}</Text>
          <Text style={styles.statLabel}>TOTAL CUSTOMERS</Text>
        </View>
      </View>

      {/* Performance Analytics — Bar Chart */}
      <View style={styles.chartCard}>
        <Text style={styles.sectionTitle}>Performance Analytics</Text>
        <View style={styles.legendRow}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: COLORS.primary }]} />
            <Text style={styles.legendText}>REVENUE</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: COLORS.surfaceContainerHighest }]} />
            <Text style={styles.legendText}>BOOKINGS</Text>
          </View>
        </View>
        <BarChart
          data={{
            labels: weeklyLabels,
            datasets: [{ data: weeklyBookingCounts.some(v => v > 0) ? weeklyBookingCounts : [0, 0, 0, 0, 0, 0, 0] }],
          }}
          width={chartWidth}
          height={180}
          chartConfig={chartConfig}
          style={styles.chart}
          fromZero
          showValuesOnTopOfBars
          withInnerLines={false}
        />
      </View>

      {/* Revenue Line Chart */}
      <View style={styles.chartCard}>
        <Text style={styles.sectionTitle}>Revenue Trend ({'\u20B9'})</Text>
        <LineChart
          data={{
            labels: weeklyLabels,
            datasets: [{ data: weeklyRevenues.some(v => v > 0) ? weeklyRevenues : [0, 0, 0, 0, 0, 0, 0] }],
          }}
          width={chartWidth}
          height={180}
          chartConfig={chartConfig}
          style={styles.chart}
          bezier
          fromZero
          withInnerLines={false}
        />
      </View>

      {/* Top Performing Services */}
      {data.service_popularity.length > 0 && (
        <View style={styles.chartCard}>
          <Text style={styles.labelTitle}>TOP PERFORMING SERVICES</Text>
          {data.service_popularity.map((s, i) => {
            const maxCount = Math.max(...data.service_popularity.map(x => x.count));
            const pct = maxCount > 0 ? (s.count / maxCount) * 100 : 0;
            return (
              <View key={s.service} style={styles.serviceRow}>
                <View style={styles.serviceInfo}>
                  <Text style={styles.serviceName}>{s.service}</Text>
                  <Text style={styles.serviceCapacity}>{Math.round(pct)}% Share</Text>
                </View>
                <View style={styles.progressTrack}>
                  <View style={[styles.progressFill, { width: `${pct}%` }]} />
                </View>
              </View>
            );
          })}
        </View>
      )}

      {/* Upcoming Appointments */}
      <View style={styles.chartCard}>
        <Text style={styles.sectionTitle}>Upcoming</Text>
        {data.upcoming_appointments.length === 0 ? (
          <Text style={styles.emptyText}>No upcoming appointments</Text>
        ) : (
          data.upcoming_appointments.map((appt) => (
            <View key={appt.id} style={styles.apptCard}>
              <View style={styles.apptAvatar}>
                <Text style={styles.apptAvatarText}>{appt.customer_name.charAt(0)}</Text>
                <View style={styles.apptStatusDot} />
              </View>
              <View style={styles.apptInfo}>
                <Text style={styles.apptName}>{appt.customer_name}</Text>
                <Text style={styles.apptService}>{appt.service.toUpperCase()}</Text>
              </View>
              <View style={styles.apptTime}>
                <Text style={styles.apptTimeText}>
                  {new Date(appt.start_time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })}
                </Text>
              </View>
            </View>
          ))
        )}
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, paddingHorizontal: 20 },
  loadingContainer: { flex: 1, backgroundColor: COLORS.bg, justifyContent: 'center', alignItems: 'center' },
  header: { paddingTop: 60, paddingBottom: 24 },
  greeting: { fontSize: 32, fontWeight: '700', color: COLORS.onSurface },
  dateText: { fontSize: 10, color: COLORS.onSurfaceVariant + '99', letterSpacing: 3, marginTop: 6 },
  statsRow: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  statCard: { flex: 1, backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12, padding: 20 },
  statIconRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  statIconBox: { width: 24, height: 24, justifyContent: 'center', alignItems: 'center' },
  statBadge: { fontSize: 9, color: COLORS.onSurfaceVariant + '80', letterSpacing: 1 },
  statLabel: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 1.5, marginTop: 4 },
  statNumber: { fontSize: 28, fontWeight: '700', color: COLORS.onSurface },
  chartCard: { backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12, padding: 20, marginBottom: 16 },
  sectionTitle: { fontSize: 20, fontWeight: '700', color: COLORS.onSurface, marginBottom: 16 },
  labelTitle: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginBottom: 16 },
  legendRow: { flexDirection: 'row', gap: 16, marginBottom: 12 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 6, height: 6, borderRadius: 3 },
  legendText: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 1.5 },
  chart: { borderRadius: 8, marginLeft: -12 },
  serviceRow: { marginBottom: 16 },
  serviceInfo: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  serviceName: { fontSize: 16, color: COLORS.onSurface },
  serviceCapacity: { fontSize: 10, color: COLORS.primary, letterSpacing: 0.5 },
  progressTrack: { height: 4, backgroundColor: COLORS.surfaceContainerHighest, borderRadius: 2, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: COLORS.primary, borderRadius: 2 },
  apptCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: COLORS.surfaceContainerLow, borderRadius: 12,
    padding: 12, marginBottom: 8, gap: 12,
  },
  apptAvatar: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: COLORS.surfaceContainerHighest,
    justifyContent: 'center', alignItems: 'center',
  },
  apptAvatarText: { fontSize: 16, fontWeight: '600', color: COLORS.onSurface },
  apptStatusDot: {
    position: 'absolute', bottom: 0, right: 0,
    width: 10, height: 10, borderRadius: 5,
    backgroundColor: COLORS.primary,
    borderWidth: 2, borderColor: COLORS.surfaceContainerLow,
  },
  apptInfo: { flex: 1 },
  apptName: { fontSize: 16, fontWeight: '500', color: COLORS.onSurface },
  apptService: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 1, marginTop: 2 },
  apptTime: {},
  apptTimeText: { fontSize: 16, fontWeight: '700', color: COLORS.primary },
  emptyText: { fontSize: 14, color: COLORS.outline, textAlign: 'center', paddingVertical: 24 },
});
