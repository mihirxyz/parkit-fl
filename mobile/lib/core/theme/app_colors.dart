import 'package:flutter/material.dart';

/// Semantic color palette for ParkIt.
/// Uses a modern dark slate palette with vivid status & FL accents.
class AppColors {
  const AppColors._();

  // Background & Surfaces
  static const Color background = Color(0xFF0A0F1D);
  static const Color surface = Color(0xFF131B2E);
  static const Color surfaceElevated = Color(0xFF1B263E);
  static const Color surfaceBorder = Color(0xFF233250);
  static const Color glassBackground = Color(0xCC131B2E);

  // Brand Accents
  static const Color primary = Color(0xFF00E5B9); // Electric Mint / Cyan
  static const Color primaryDark = Color(0xFF00A887);
  static const Color primaryLight = Color(0xFF5DFFD6);
  static const Color secondary = Color(0xFF6366F1); // Indigo / FL Accent
  static const Color accentPurple = Color(0xFF8B5CF6);

  // Occupancy Status Gradients & Tints
  static const Color occupancyLow = Color(0xFF10B981); // Emerald (<50%)
  static const Color occupancyMedium = Color(0xFFF59E0B); // Amber (50-80%)
  static const Color occupancyHigh = Color(0xFFEF4444); // Crimson (>80%)

  // Zone Type Colors
  static const Color structuredZone = Color(0xFF3B82F6); // Blue
  static const Color unstructuredZone = Color(0xFF8B5CF6); // Violet

  // Vehicle States
  static const Color stateParked = Color(0xFF10B981); // Green
  static const Color stateMoving = Color(0xFF38BDF8); // Sky Blue

  // Text & Typography
  static const Color textPrimary = Color(0xFFF8FAFC);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF64748B);

  // Chart Accents
  static const Color flCurve = Color(0xFF00E5B9);
  static const Color centralizedBaseline = Color(0xFFF59E0B);

  /// Dynamic helper returning color corresponding to occupancy rate (0.0 to 1.0)
  static Color forOccupancy(double rate) {
    if (rate < 0.50) return occupancyLow;
    if (rate < 0.80) return occupancyMedium;
    return occupancyHigh;
  }

  /// Dynamic helper returning polygon fill color with balanced alpha
  static Color polygonFill(double rate, {int alpha = 70}) {
    return forOccupancy(rate).withAlpha(alpha);
  }
}
