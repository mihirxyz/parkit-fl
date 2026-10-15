import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';

import '../core/theme/app_colors.dart';
import '../core/theme/app_typography.dart';
import '../providers/parking_provider.dart';
import '../widgets/cards/parking_option_card.dart';
import 'vehicle_simulator_sheet.dart';
import 'zone_detail_screen.dart';
import 'zone_map_screen.dart';

/// Friendly, non-technical home screen answering "where can I park?"
class HomeDashboardScreen extends StatefulWidget {
  const HomeDashboardScreen({super.key});

  @override
  State<HomeDashboardScreen> createState() => _HomeDashboardScreenState();
}

class _HomeDashboardScreenState extends State<HomeDashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ParkingProvider>().fetchZones();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ParkingProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.local_parking_rounded,
                color: AppColors.primary,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Text('ParkIt', style: AppTypography.titleLarge),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline_rounded),
            onPressed: () => _showInfoDialog(context),
            tooltip: 'About ParkIt',
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => provider.fetchZones(),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: provider.isLoading && provider.zones.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : provider.hasError && provider.zones.isEmpty
              ? _buildErrorState(provider)
              : _buildContent(context, provider),
    );
  }

  Widget _buildContent(BuildContext context, ParkingProvider provider) {
    final totalAvailable = provider.totalAvailable;
    final zoneCount = provider.zones.length;

    // Sort zones by most available first (lowest occupancy)
    final sortedZones = List.of(provider.zones)
      ..sort((a, b) => a.occupancyRate.compareTo(b.occupancyRate));

    // Take top 3-4 zones with best availability
    final topZones = sortedZones.take(4).toList();

    return RefreshIndicator(
      onRefresh: () => provider.fetchZones(),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Hero headline
            _buildHeadline(totalAvailable, zoneCount),
            const SizedBox(height: 20),

            // Value proposition chip
            _buildValuePropChip(),
            const SizedBox(height: 32),

            // Section header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Best Options',
                  style: AppTypography.displayMedium.copyWith(fontSize: 20),
                ),
                TextButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const ZoneMapScreen(),
                    ),
                  ),
                  icon: const Icon(Icons.map_outlined, size: 16),
                  label: const Text('View Map'),
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.primary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Top parking options
            ...topZones.asMap().entries.map((entry) {
              final index = entry.key;
              final zone = entry.value;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: ParkingOptionCard(
                  zone: zone,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ZoneDetailScreen(zone: zone),
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(
                      duration: const Duration(milliseconds: 400),
                      delay: Duration(milliseconds: 100 + index * 90),
                      curve: Curves.easeOutQuad,
                    )
                    .slideY(
                      begin: 0.15,
                      end: 0,
                      duration: const Duration(milliseconds: 400),
                      delay: Duration(milliseconds: 100 + index * 90),
                      curve: Curves.easeOutQuad,
                    ),
              );
            }),

            const SizedBox(height: 24),

            // View full map button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const ZoneMapScreen(),
                  ),
                ),
                icon: const Icon(Icons.map_rounded),
                label: const Text('View Full Zone Map'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: AppColors.background,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 12),

            // Simulate telemetry button (secondary)
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (_) => const VehicleSimulatorSheet(),
                ),
                icon: const Icon(Icons.sensors_rounded),
                label: const Text('Simulate Vehicle Telemetry'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.primary,
                  side: const BorderSide(color: AppColors.primary),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeadline(int totalAvailable, int zoneCount) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Icon(
              totalAvailable > 0
                  ? Icons.check_circle_rounded
                  : Icons.warning_rounded,
              size: 38,
              color: totalAvailable > 0
                  ? AppColors.occupancyLow
                  : AppColors.occupancyMedium,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: totalAvailable > 0
                  ? TweenAnimationBuilder<int>(
                      tween: IntTween(begin: 0, end: totalAvailable),
                      duration: const Duration(milliseconds: 1000),
                      curve: Curves.easeOutCubic,
                      builder: (context, value, child) {
                        return RichText(
                          text: TextSpan(
                            children: [
                              TextSpan(
                                text: '$value ',
                                style: AppTypography.displayLarge.copyWith(
                                  fontSize: 38,
                                  fontWeight: FontWeight.w900,
                                  color: AppColors.textPrimary,
                                  height: 1.1,
                                ),
                              ),
                              TextSpan(
                                text: value == 1
                                    ? 'spot available now'
                                    : 'spots available now',
                                style: AppTypography.displayLarge.copyWith(
                                  fontSize: 24,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.textPrimary,
                                  height: 1.1,
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    )
                  : Text(
                      'All zones currently full',
                      style: AppTypography.displayLarge.copyWith(fontSize: 28),
                    ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Padding(
          padding: const EdgeInsets.only(left: 52),
          child: Text(
            totalAvailable > 0
                ? 'across $zoneCount parking zones in Pune'
                : 'Check back soon for availability',
            style: AppTypography.bodyLarge.copyWith(
              color: AppColors.textMuted,
              fontSize: 15,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildValuePropChip() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surfaceElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppColors.surfaceBorder,
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.privacy_tip_outlined,
            size: 18,
            color: AppColors.primary,
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              'Real-time predictions • Powered by on-device AI • No centralized tracking',
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(ParkingProvider provider) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline_rounded,
              size: 64,
              color: AppColors.occupancyHigh,
            ),
            const SizedBox(height: 16),
            Text(
              'Unable to load parking data',
              style: AppTypography.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              provider.errorMessage ?? 'Connection error',
              style: AppTypography.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => provider.fetchZones(),
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Try Again'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.background,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showInfoDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.local_parking_rounded,
                color: AppColors.primary,
                size: 18,
              ),
            ),
            const SizedBox(width: 12),
            Text('About ParkIt', style: AppTypography.titleLarge),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'ParkIt shows real-time parking availability using Federated Learning — a privacy-first AI approach.',
              style: AppTypography.bodyLarge,
            ),
            const SizedBox(height: 12),
            Text(
              'How it works:',
              style: AppTypography.titleMedium.copyWith(fontSize: 14),
            ),
            const SizedBox(height: 8),
            _buildInfoBullet('Vehicle sensors detect parking patterns locally'),
            _buildInfoBullet('Models train on your device, not in the cloud'),
            _buildInfoBullet('Only model updates are shared, never raw location data'),
            _buildInfoBullet('Everyone benefits from collective learning without sacrificing privacy'),
            const SizedBox(height: 12),
            Text(
              'Tap "How It Works" in the bottom nav to see technical details and model performance.',
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.textMuted,
                fontSize: 12,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoBullet(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 5,
            height: 5,
            margin: const EdgeInsets.only(top: 7, right: 8),
            decoration: const BoxDecoration(
              color: AppColors.primary,
              shape: BoxShape.circle,
            ),
          ),
          Expanded(
            child: Text(
              text,
              style: AppTypography.bodyMedium.copyWith(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

