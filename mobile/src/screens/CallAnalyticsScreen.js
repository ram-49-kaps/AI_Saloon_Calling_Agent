// Call Analytics Screen — AI Agent Performance Dashboard
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, RefreshControl,
  TouchableOpacity, ActivityIndicator, Modal,
} from 'react-native';
import { COLORS, FONTS, RADIUS } from '../config';
import { getCallAnalytics, getCallLogs } from '../services/api';

export default function CallAnalyticsScreen() {
  const [analytics, setAnalytics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(7);
  const [filter, setFilter] = useState('all'); // 'all', 'failed', 'low_rated'
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [analyticsData, logsData] = await Promise.all([
        getCallAnalytics(period),
        getCallLogs({
          limit: 20,
          ...(filter === 'failed' ? { onlyFailed: true } : {}),
          ...(filter === 'low_rated' ? { ratingMax: 2 } : {}),
        }),
      ]);
      setAnalytics(analyticsData);
      setLogs(logsData.call_logs || []);
    } catch (e) {
      console.log('Analytics error:', e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [period, filter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const onRefresh = () => { setRefreshing(true); fetchData(); };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  const ratingStars = (rating) => {
    if (!rating) return '--';
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  const successRate = analytics?.booking_success_rate || 0;
  const rateColor = successRate >= 80 ? COLORS.success : successRate >= 50 ? COLORS.primary : COLORS.error;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>AI Agent Analytics</Text>
        <Text style={styles.subtitle}>PERFORMANCE & FEEDBACK</Text>
      </View>

      {/* Period Selector */}
      <View style={styles.periodRow}>
        {[7, 14, 30].map((d) => (
          <TouchableOpacity
            key={d}
            style={[styles.periodBtn, period === d && styles.periodBtnActive]}
            onPress={() => { setPeriod(d); setLoading(true); }}
          >
            <Text style={[styles.periodText, period === d && styles.periodTextActive]}>
              {d}D
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {analytics && (
        <>
          {/* Key Metrics */}
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{analytics.total_calls}</Text>
              <Text style={styles.metricLabel}>TOTAL CALLS</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={[styles.metricValue, { color: rateColor }]}>
                {successRate}%
              </Text>
              <Text style={styles.metricLabel}>BOOKING RATE</Text>
            </View>
          </View>

          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {analytics.avg_feedback_rating > 0 ? `${analytics.avg_feedback_rating}/5` : '--'}
              </Text>
              <Text style={styles.metricLabel}>AVG RATING</Text>
              {analytics.total_rated_calls > 0 && (
                <Text style={styles.metricSub}>{analytics.total_rated_calls} rated</Text>
              )}
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{formatDuration(analytics.avg_duration_seconds)}</Text>
              <Text style={styles.metricLabel}>AVG DURATION</Text>
            </View>
          </View>

          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{analytics.successful_bookings}</Text>
              <Text style={styles.metricLabel}>BOOKINGS MADE</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={[styles.metricValue, analytics.calls_with_errors > 0 && { color: COLORS.error }]}>
                {analytics.calls_with_errors}
              </Text>
              <Text style={styles.metricLabel}>CALLS W/ ERRORS</Text>
            </View>
          </View>

          {/* AI Performance Bar */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Booking Success Rate</Text>
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${Math.min(successRate, 100)}%`, backgroundColor: rateColor }]} />
            </View>
            <View style={styles.progressLabels}>
              <Text style={styles.progressLabel}>0%</Text>
              <Text style={[styles.progressLabel, { color: rateColor, fontWeight: '700' }]}>{successRate}%</Text>
              <Text style={styles.progressLabel}>100%</Text>
            </View>
          </View>

          {/* Cost Summary */}
          {analytics.total_cost > 0 && (
            <View style={styles.card}>
              <View style={styles.costRow}>
                <Text style={styles.costLabel}>Total Vapi Cost ({period} days)</Text>
                <Text style={styles.costValue}>${analytics.total_cost}</Text>
              </View>
              {analytics.total_calls > 0 && (
                <View style={styles.costRow}>
                  <Text style={styles.costLabel}>Cost per Call</Text>
                  <Text style={styles.costValue}>
                    ${(analytics.total_cost / analytics.total_calls).toFixed(3)}
                  </Text>
                </View>
              )}
            </View>
          )}
        </>
      )}

      {/* Call Logs Section */}
      <View style={styles.logsHeader}>
        <Text style={styles.sectionTitle}>Recent Calls</Text>
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        {[
          { key: 'all', label: 'ALL' },
          { key: 'failed', label: 'FAILED' },
          { key: 'low_rated', label: 'LOW RATED' },
        ].map((f) => (
          <TouchableOpacity
            key={f.key}
            style={[styles.filterBtn, filter === f.key && styles.filterBtnActive]}
            onPress={() => { setFilter(f.key); setLoading(true); }}
          >
            <Text style={[styles.filterText, filter === f.key && styles.filterTextActive]}>
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Call Log Cards */}
      {logs.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No call logs yet</Text>
          <Text style={styles.emptySubtext}>Calls will appear here after customers interact with the AI agent</Text>
        </View>
      ) : (
        logs.map((log) => (
          <TouchableOpacity
            key={log.id}
            style={styles.logCard}
            onPress={() => setSelectedLog(log)}
            activeOpacity={0.7}
          >
            <View style={styles.logTop}>
              <View style={styles.logLeft}>
                <View style={[styles.logStatus, { backgroundColor: log.booking_succeeded ? COLORS.success + '20' : COLORS.error + '20' }]}>
                  <View style={[styles.logStatusDot, { backgroundColor: log.booking_succeeded ? COLORS.success : COLORS.error }]} />
                  <Text style={[styles.logStatusText, { color: log.booking_succeeded ? COLORS.success : COLORS.error }]}>
                    {log.booking_succeeded ? 'BOOKED' : 'NO BOOKING'}
                  </Text>
                </View>
              </View>
              <Text style={styles.logDuration}>{formatDuration(log.duration_seconds)}</Text>
            </View>

            <View style={styles.logMid}>
              {log.phone_number ? (
                <Text style={styles.logPhone}>{log.phone_number}</Text>
              ) : (
                <Text style={styles.logPhone}>Unknown caller</Text>
              )}
              {log.feedback_rating && (
                <Text style={[styles.logRating, log.feedback_rating <= 2 && { color: COLORS.error }]}>
                  {ratingStars(log.feedback_rating)}
                </Text>
              )}
            </View>

            {log.summary && (
              <Text style={styles.logSummary} numberOfLines={2}>{log.summary}</Text>
            )}

            <View style={styles.logBottom}>
              <Text style={styles.logMeta}>
                {log.tool_calls_count} tool calls
                {log.tool_errors_count > 0 && ` · ${log.tool_errors_count} errors`}
              </Text>
              {log.created_at && (
                <Text style={styles.logTime}>
                  {new Date(log.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                  {' '}
                  {new Date(log.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}
                </Text>
              )}
            </View>
          </TouchableOpacity>
        ))
      )}

      <View style={{ height: 100 }} />

      {/* Transcript Modal */}
      <Modal visible={!!selectedLog} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Call Transcript</Text>
              <TouchableOpacity onPress={() => setSelectedLog(null)} style={styles.modalClose}>
                <Text style={styles.modalCloseText}>Close</Text>
              </TouchableOpacity>
            </View>

            {selectedLog && (
              <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
                <View style={styles.modalMeta}>
                  <Text style={styles.modalMetaText}>
                    Duration: {formatDuration(selectedLog.duration_seconds)}
                  </Text>
                  <Text style={styles.modalMetaText}>
                    Status: {selectedLog.booking_succeeded ? 'Booking Made' : 'No Booking'}
                  </Text>
                  {selectedLog.feedback_rating && (
                    <Text style={styles.modalMetaText}>
                      Rating: {ratingStars(selectedLog.feedback_rating)} ({selectedLog.feedback_rating}/5)
                    </Text>
                  )}
                  {selectedLog.ended_reason && (
                    <Text style={styles.modalMetaText}>
                      Ended: {selectedLog.ended_reason}
                    </Text>
                  )}
                </View>

                <Text style={styles.transcriptLabel}>TRANSCRIPT</Text>
                <Text style={styles.transcriptText}>
                  {selectedLog.transcript || 'No transcript available'}
                </Text>

                {selectedLog.summary && (
                  <>
                    <Text style={styles.transcriptLabel}>AI SUMMARY</Text>
                    <Text style={styles.transcriptText}>{selectedLog.summary}</Text>
                  </>
                )}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, paddingHorizontal: 20 },
  loadingContainer: { flex: 1, backgroundColor: COLORS.bg, justifyContent: 'center', alignItems: 'center' },

  header: { paddingTop: 60, paddingBottom: 16 },
  title: { fontSize: 28, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },
  subtitle: { fontSize: 10, color: COLORS.onSurfaceVariant + '99', letterSpacing: 3, marginTop: 4 },

  periodRow: { flexDirection: 'row', gap: 8, marginBottom: 20 },
  periodBtn: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: RADIUS.full, backgroundColor: COLORS.surfaceContainerLow },
  periodBtnActive: { backgroundColor: COLORS.primary },
  periodText: { fontSize: 13, fontWeight: '600', color: COLORS.outline },
  periodTextActive: { color: COLORS.onPrimary },

  metricsGrid: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  metricCard: { flex: 1, backgroundColor: COLORS.surfaceContainerLow, borderRadius: RADIUS.xl, padding: 20 },
  metricValue: { fontSize: 28, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },
  metricLabel: { fontSize: 9, color: COLORS.onSurfaceVariant, letterSpacing: 1.5, marginTop: 4 },
  metricSub: { fontSize: 10, color: COLORS.outline, marginTop: 2 },

  card: { backgroundColor: COLORS.surfaceContainerLow, borderRadius: RADIUS.xl, padding: 20, marginBottom: 16 },
  cardTitle: { fontSize: 14, fontWeight: '600', color: COLORS.onSurface, marginBottom: 12 },

  progressTrack: { height: 8, backgroundColor: COLORS.surfaceContainerHighest, borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 4 },
  progressLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  progressLabel: { fontSize: 10, color: COLORS.outline },

  costRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: COLORS.outlineVariant + '30' },
  costLabel: { fontSize: 14, color: COLORS.onSurfaceVariant },
  costValue: { fontSize: 14, fontWeight: '700', color: COLORS.primary },

  logsHeader: { marginTop: 8, marginBottom: 8 },
  sectionTitle: { fontSize: 20, fontWeight: '700', color: COLORS.onSurface, fontFamily: FONTS.display },

  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  filterBtn: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: RADIUS.full, backgroundColor: COLORS.surfaceContainerLow },
  filterBtnActive: { backgroundColor: COLORS.primary },
  filterText: { fontSize: 11, fontWeight: '600', color: COLORS.outline, letterSpacing: 0.5 },
  filterTextActive: { color: COLORS.onPrimary },

  emptyCard: { backgroundColor: COLORS.surfaceContainerLow, borderRadius: RADIUS.xl, padding: 32, alignItems: 'center' },
  emptyText: { fontSize: 16, color: COLORS.outline, marginBottom: 4 },
  emptySubtext: { fontSize: 12, color: COLORS.outline + '80', textAlign: 'center' },

  logCard: { backgroundColor: COLORS.surfaceContainerLow, borderRadius: RADIUS.lg, padding: 16, marginBottom: 10 },
  logTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  logLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  logStatus: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 4, borderRadius: RADIUS.full },
  logStatusDot: { width: 6, height: 6, borderRadius: 3 },
  logStatusText: { fontSize: 10, fontWeight: '700', letterSpacing: 0.5 },
  logDuration: { fontSize: 12, color: COLORS.outline, fontWeight: '600' },

  logMid: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  logPhone: { fontSize: 15, fontWeight: '500', color: COLORS.onSurface },
  logRating: { fontSize: 13, color: COLORS.primary },

  logSummary: { fontSize: 12, color: COLORS.onSurfaceVariant, marginBottom: 8, lineHeight: 18 },

  logBottom: { flexDirection: 'row', justifyContent: 'space-between' },
  logMeta: { fontSize: 10, color: COLORS.outline },
  logTime: { fontSize: 10, color: COLORS.outline },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: COLORS.surfaceContainerLow, borderTopLeftRadius: 24, borderTopRightRadius: 24, maxHeight: '85%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, borderBottomWidth: 1, borderBottomColor: COLORS.outlineVariant + '30' },
  modalTitle: { fontSize: 18, fontWeight: '700', color: COLORS.onSurface },
  modalClose: { paddingHorizontal: 16, paddingVertical: 8, backgroundColor: COLORS.surfaceContainerHighest, borderRadius: RADIUS.full },
  modalCloseText: { fontSize: 13, fontWeight: '600', color: COLORS.onSurface },
  modalBody: { padding: 20 },
  modalMeta: { backgroundColor: COLORS.surfaceContainer, borderRadius: RADIUS.lg, padding: 16, marginBottom: 16 },
  modalMetaText: { fontSize: 13, color: COLORS.onSurfaceVariant, marginBottom: 4 },
  transcriptLabel: { fontSize: 10, color: COLORS.onSurfaceVariant, letterSpacing: 2, marginBottom: 8, marginTop: 8 },
  transcriptText: { fontSize: 14, color: COLORS.onSurface, lineHeight: 22 },
});
