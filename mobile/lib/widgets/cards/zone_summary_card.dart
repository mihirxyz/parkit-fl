import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';
import '../../models/parking_zone.dart';

/// Compact zone card used in horizontal carousel at the bottom of the map view.
class ZoneSummaryCard extends StatelessWidget {
  final ParkingZone zone;
  final bool isSelected;
  final VoidCallback onTap;

  const ZoneSummaryCard({
    super.key,
    required this.zone,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final occupancyColor = AppColors.forOccupancy(zone.occupancyRate);
    final percent = (zone.occupancyRate * 100).toInt();

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          width: 270,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isSelected
                ? AppColors.surfaceElevated
                : AppColors.glassBackground,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected ? AppColors.primary : AppColors.surfaceBorder,
              width: isSelected ? 2 : 1,
            ),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: AppColors.primary.withAlpha(40),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    )
                  ]
                : [],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      zone.name ?? zone.zoneId,
                      style: AppTypography.titleMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: (zone.isStructured
                              ? AppColors.structuredZone
                              : AppColors.unstructuredZone)
                          .withAlpha(30),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: (zone.isStructured
                                ? AppColors.structuredZone
                                : AppColors.unstructuredZone)
                            .withAlpha(80),
                        width: 0.8,
                      ),
                    ),
                    child: Text(
                      zone.zoneType.toUpperCase(),
                      style: TextStyle(
                        color: zone.isStructured
                            ? AppColors.structuredZone
                            : AppColors.unstructuredZone,
                        fontSize: 9,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Occupancy', style: AppTypography.labelSmall),
                      Text(
                        '$percent%',
                        style: TextStyle(
                          color: occupancyColor,
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: zone.occupancyRate.clamp(0.0, 1.0),
                      minHeight: 6,
                      backgroundColor: AppColors.surfaceElevated,
                      valueColor: AlwaysStoppedAnimation<Color>(occupancyColor),
                    ),
                  ),
                ],
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.local_parking_rounded,
                          size: 14, color: AppColors.stateParked),
                      const SizedBox(width: 4),
                      Text(
                        '${zone.parkedVehicles}/${zone.totalCapacity} Parked',
                        style: AppTypography.numericSub,
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      const Icon(Icons.directions_car_rounded,
                          size: 14, color: AppColors.stateMoving),
                      const SizedBox(width: 4),
                      Text(
                        '${zone.movingVehicles} Moving',
                        style: AppTypography.numericSub,
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
