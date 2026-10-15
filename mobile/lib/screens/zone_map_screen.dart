import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';

import '../core/constants/api_constants.dart';
import '../core/theme/app_colors.dart';
import '../core/theme/app_typography.dart';
import '../models/parking_zone.dart';
import '../providers/parking_provider.dart';
import '../widgets/cards/zone_summary_card.dart';
import '../widgets/feedback/custom_shimmer.dart';
import '../widgets/map/map_controls.dart';
import '../widgets/map/zone_polygon_layer.dart';
import 'vehicle_simulator_sheet.dart';
import 'zone_detail_screen.dart';

/// Technical zone map screen with detailed spatial view, occupancy metrics, and filter controls.
class ZoneMapScreen extends StatefulWidget {
  const ZoneMapScreen({super.key});

  @override
  State<ZoneMapScreen> createState() => _ZoneMapScreenState();
}

class _ZoneMapScreenState extends State<ZoneMapScreen> {
  late final MapController _mapController;

  @override
  void initState() {
    super.initState();
    _mapController = MapController();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ParkingProvider>().fetchZones();
    });
  }

  void _recenterMap() {
    _mapController.move(
      const LatLng(ApiConstants.puneCenterLat, ApiConstants.puneCenterLon),
      ApiConstants.defaultZoom,
    );
  }

  void _zoomIn() {
    final currentZoom = _mapController.camera.zoom;
    _mapController.move(_mapController.camera.center, currentZoom + 0.75);
  }

  void _zoomOut() {
    final currentZoom = _mapController.camera.zoom;
    _mapController.move(_mapController.camera.center, currentZoom - 0.75);
  }

  void _onZoneTapped(ParkingZone zone) {
    context.read<ParkingProvider>().selectZone(zone);
    _mapController.move(zone.center, 17.5);
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ZoneDetailScreen(zone: zone),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ParkingProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Stack(
        children: [
          // OpenStreetMap Layer
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const LatLng(
                ApiConstants.puneCenterLat,
                ApiConstants.puneCenterLon,
              ),
              initialZoom: ApiConstants.defaultZoom,
              minZoom: ApiConstants.minZoom,
              maxZoom: ApiConstants.maxZoom,
              onTap: (_, __) {
                provider.selectZone(null);
              },
            ),
            children: [
              // OpenStreetMap with dark filter overlay
              ColorFiltered(
                colorFilter: ColorFilter.matrix([
                  0.35, 0, 0, 0, 0,     // Red channel - reduced intensity
                  0, 0.35, 0, 0, 0,     // Green channel - reduced intensity
                  0, 0, 0.40, 0, 0,     // Blue channel - slightly more blue for cooler tone
                  0, 0, 0, 1, 0,        // Alpha channel - unchanged
                ]),
                child: TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.parkit.mobile',
                ),
              ),
              // OSM attribution
              Align(
                alignment: Alignment.bottomLeft,
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.surface.withOpacity(0.7),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      '© OpenStreetMap contributors',
                      style: TextStyle(
                        fontSize: 9,
                        color: AppColors.textMuted,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ),
              ),
              if (provider.filteredZones.isNotEmpty) ...[
                PolygonLayer(
                  polygons: ZoneMapLayers.buildPolygons(
                    zones: provider.filteredZones,
                    selectedZone: provider.selectedZone,
                    onZoneSelected: _onZoneTapped,
                  ),
                ),
                MarkerLayer(
                  markers: ZoneMapLayers.buildZoneLabels(
                    zones: provider.filteredZones,
                    selectedZone: provider.selectedZone,
                    onZoneSelected: _onZoneTapped,
                  ),
                ),
              ],
            ],
          ),
          // Top Bar Header Overlay
          Positioned(
            top: MediaQuery.of(context).padding.top + 10,
            left: 16,
            right: 16,
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: AppColors.glassBackground,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.surfaceBorder),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withAlpha(30),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.local_parking_rounded, color: AppColors.primary, size: 20),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('ParkIt Pune Grid', style: AppTypography.titleMedium),
                            Text(
                              '${provider.totalParked}/${provider.totalCapacity} Occupied • ${(provider.overallOccupancyRate * 100).toInt()}% Rate',
                              style: AppTypography.labelSmall.copyWith(color: AppColors.primary),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.refresh_rounded, color: AppColors.textPrimary, size: 20),
                        onPressed: () => provider.fetchZones(),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildFilterChip('All Zones', 'all', provider),
                      const SizedBox(width: 8),
                      _buildFilterChip('Structured', 'structured', provider),
                      const SizedBox(width: 8),
                      _buildFilterChip('Unstructured', 'unstructured', provider),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Floating Map Controls
          Positioned(
            right: 16,
            top: MediaQuery.of(context).padding.top + 130,
            child: MapControls(
              onZoomIn: _zoomIn,
              onZoomOut: _zoomOut,
              onRecenter: _recenterMap,
              onRefresh: () => provider.fetchZones(),
            ),
          ),

          // Bottom Zone Carousel & Telemetry FAB
          Positioned(
            left: 0,
            right: 0,
            bottom: 16,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Padding(
                  padding: const EdgeInsets.only(right: 16, bottom: 12),
                  child: FloatingActionButton.extended(
                    heroTag: 'simulate_fab',
                    backgroundColor: AppColors.primary,
                    foregroundColor: AppColors.background,
                    icon: const Icon(Icons.sensors_rounded, size: 20),
                    label: const Text('Simulate Telemetry', style: TextStyle(fontWeight: FontWeight.bold)),
                    onPressed: () {
                      showModalBottomSheet(
                        context: context,
                        isScrollControlled: true,
                        backgroundColor: Colors.transparent,
                        builder: (_) => const VehicleSimulatorSheet(),
                      );
                    },
                  ),
                ),
                if (provider.isLoading && provider.zones.isEmpty)
                  const SizedBox(height: 140, child: ZoneCardListSkeleton())
                else if (provider.hasError && provider.zones.isEmpty)
                  Container(
                    margin: const EdgeInsets.symmetric(horizontal: 16),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.occupancyHigh),
                    ),
                    child: Text(provider.errorMessage ?? 'Connection error', style: AppTypography.bodyMedium),
                  )
                else
                  SizedBox(
                    height: 140,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: provider.filteredZones.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 12),
                      itemBuilder: (ctx, index) {
                        final zone = provider.filteredZones[index];
                        final isSelected = provider.selectedZone?.zoneId == zone.zoneId;
                        return ZoneSummaryCard(
                          zone: zone,
                          isSelected: isSelected,
                          onTap: () => _onZoneTapped(zone),
                        );
                      },
                    ),
                  ),
              ],
            ),
          ),

        ],
      ),
    );
  }
  Widget _buildFilterChip(String label, String type, ParkingProvider provider) {
    final isSelected = provider.filterType == type;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => provider.setFilterType(type),
      backgroundColor: AppColors.glassBackground,
      selectedColor: AppColors.primary.withAlpha(50),
      labelStyle: TextStyle(
        color: isSelected ? AppColors.primary : AppColors.textSecondary,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        fontSize: 12,
      ),
      side: BorderSide(
        color: isSelected ? AppColors.primary : AppColors.surfaceBorder,
      ),
    );
  }

}
