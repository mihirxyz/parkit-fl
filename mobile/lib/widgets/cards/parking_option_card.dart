import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';
import '../../models/parking_zone.dart';
import '../../utils/zone_name_helper.dart';

/// Simple, friendly card showing parking availability for home screen
class ParkingOptionCard extends StatelessWidget {
  final ParkingZone zone;
  final VoidCallback onTap;

  const ParkingOptionCard({
    super.key,
    required this.zone,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final friendlyName = ZoneNameHelper.getFriendlyName(zone.zoneId, zone.name);
    final available = zone.availableSpots;
    final occupancyRate = zone.occupancyRate;

    // Determine simple status
    String statusText;
    Color statusColor;
    IconData statusIcon;

    if (occupancyRate >= 0.90) {
      statusText = 'Full';
      statusColor = AppColors.occupancyHigh;
      statusIcon = Icons.block_rounded;
    } else if (occupancyRate >= 0.70) {
      statusText = 'Filling Up';
      statusColor = AppColors.occupancyMedium;
      statusIcon = Icons.warning_rounded;
    } else {
      statusText = 'Available';
      statusColor = AppColors.occupancyLow;
      statusIcon = Icons.check_circle_rounded;
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.glassBackground,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppColors.surfaceBorder,
              width: 1,
            ),
          ),
          child: Row(
            children: [
              // Status icon
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  statusIcon,
                  color: statusColor,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              // Zone info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      friendlyName,
                      style: AppTypography.titleMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                              color: statusColor.withValues(alpha: 0.3),
                              width: 0.5,
                            ),
                          ),
                          child: Text(
                            statusText,
                            style: TextStyle(
                              color: statusColor,
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          available > 0
                              ? '$available ${available == 1 ? 'spot' : 'spots'} open'
                              : 'No spots available',
                          style: AppTypography.bodyMedium,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              // Arrow
              Icon(
                Icons.arrow_forward_ios_rounded,
                size: 16,
                color: AppColors.textMuted,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
