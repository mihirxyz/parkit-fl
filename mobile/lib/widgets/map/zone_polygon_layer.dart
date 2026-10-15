import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import '../../core/theme/app_colors.dart';
import '../../models/parking_zone.dart';

/// Helper builder producing styled polygon and marker layers for flutter_map.
class ZoneMapLayers {
  const ZoneMapLayers._();

  static List<Polygon> buildPolygons({
    required List<ParkingZone> zones,
    required ParkingZone? selectedZone,
    required Function(ParkingZone) onZoneSelected,
  }) {
    return zones.map((zone) {
      final isSelected = selectedZone?.zoneId == zone.zoneId;
      final occupancyColor = AppColors.forOccupancy(zone.occupancyRate);

      return Polygon(
        points: zone.polygonPoints,
        color: occupancyColor.withAlpha(isSelected ? 110 : 65),
        borderColor: isSelected ? AppColors.primary : occupancyColor,
        borderStrokeWidth: isSelected ? 3.0 : 1.5,
      );
    }).toList();
  }

  static List<Marker> buildZoneLabels({
    required List<ParkingZone> zones,
    required ParkingZone? selectedZone,
    required Function(ParkingZone) onZoneSelected,
  }) {
    return zones.map((zone) {
      final isSelected = selectedZone?.zoneId == zone.zoneId;
      final percent = (zone.occupancyRate * 100).toInt();
      final occupancyColor = AppColors.forOccupancy(zone.occupancyRate);

      return Marker(
        point: zone.center,
        width: 90,
        height: 48,
        child: GestureDetector(
          onTap: () => onZoneSelected(zone),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: isSelected 
                  ? AppColors.surface.withValues(alpha: 0.85) 
                  : AppColors.glassBackground.withValues(alpha: 0.7),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: isSelected ? AppColors.primary.withValues(alpha: 0.8) : AppColors.surfaceBorder.withValues(alpha: 0.6),
                width: isSelected ? 1.5 : 0.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.15),
                  blurRadius: 8,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  zone.name ?? zone.zoneId,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: isSelected ? AppColors.primary : AppColors.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  '$percent% • ${zone.parkedVehicles}/${zone.totalCapacity}',
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                    color: occupancyColor,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }).toList();
  }
}
