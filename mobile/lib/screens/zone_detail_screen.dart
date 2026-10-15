import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_colors.dart';
import '../core/theme/app_typography.dart';
import '../models/parking_zone.dart';
import '../providers/parking_provider.dart';
import '../widgets/cards/metric_stat_card.dart';
import '../widgets/cards/reading_tile.dart';
import '../widgets/charts/occupancy_radial_gauge.dart';
import 'vehicle_simulator_sheet.dart';

class ZoneDetailScreen extends StatefulWidget {
  final ParkingZone zone;
  const ZoneDetailScreen({super.key, required this.zone});

  @override
  State<ZoneDetailScreen> createState() => _ZoneDetailScreenState();
}

class _ZoneDetailScreenState extends State<ZoneDetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ParkingProvider>().loadZoneDetail(widget.zone.zoneId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ParkingProvider>();
    final currentZone = (provider.selectedZone?.zoneId == widget.zone.zoneId)
        ? provider.selectedZone!
        : widget.zone;
    final isStructured = currentZone.isStructured;
    final zoneTypeColor =
        isStructured ? AppColors.structuredZone : AppColors.unstructuredZone;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(currentZone.name ?? currentZone.zoneId,
            style: AppTypography.titleLarge),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => provider.loadZoneDetail(currentZone.zoneId),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.background,
        icon: const Icon(Icons.sensors_rounded, size: 20),
        label: const Text('Simulate Telemetry',
            style: TextStyle(fontWeight: FontWeight.bold)),
        onPressed: () {
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            backgroundColor: Colors.transparent,
            builder: (_) => const VehicleSimulatorSheet(),
          );
        },
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: zoneTypeColor.withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: zoneTypeColor.withAlpha(90)),
                  ),
                  child: Text(
                    currentZone.zoneType.toUpperCase(),
                    style: TextStyle(
                      color: zoneTypeColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceElevated,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.surfaceBorder),
                  ),
                  child: Text('ID: ${currentZone.zoneId}', style: AppTypography.numericSub),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.surfaceBorder),
              ),
              child: Row(
                children: [
                  OccupancyRadialGauge(
                    occupancyRate: currentZone.occupancyRate,
                    parked: currentZone.parkedVehicles,
                    total: currentZone.totalCapacity,
                    size: 110,
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Zone Occupancy', style: AppTypography.titleMedium),
                        const SizedBox(height: 4),
                        Text(
                          'Available Spots: ${currentZone.availableSpots}',
                          style: AppTypography.bodyMedium,
                        ),
                        Text(
                          'Total Capacity: ${currentZone.totalCapacity}',
                          style: AppTypography.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: MetricStatCard(
                    title: 'Parked',
                    value: '${currentZone.parkedVehicles}',
                    icon: Icons.local_parking_rounded,
                    accentColor: AppColors.stateParked,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: MetricStatCard(
                    title: 'Moving',
                    value: '${currentZone.movingVehicles}',
                    icon: Icons.directions_car_rounded,
                    accentColor: AppColors.stateMoving,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: MetricStatCard(
                    title: 'Available Spots',
                    value: '${currentZone.availableSpots}',
                    icon: Icons.check_circle_outline_rounded,
                    accentColor: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: MetricStatCard(
                    title: 'Total Ingested',
                    value: '${currentZone.totalVehicles}',
                    icon: Icons.hub_rounded,
                    accentColor: AppColors.secondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Text('RECENT VEHICLE TELEMETRY', style: AppTypography.labelSmall),
            const SizedBox(height: 8),
            if (currentZone.recentReadings.isEmpty)
              Container(
                padding: const EdgeInsets.all(20),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'No recent telemetry records in this zone.\nTap "Simulate Telemetry" below.',
                  style: AppTypography.bodyMedium,
                  textAlign: TextAlign.center,
                ),
              )
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: currentZone.recentReadings.length,
                itemBuilder: (ctx, i) => ReadingTile(
                  reading: currentZone.recentReadings[i],
                ),
              ),
            const SizedBox(height: 80),

          ],
        ),
      ),
    );
  }
}
