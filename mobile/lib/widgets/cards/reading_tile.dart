import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';
import '../../models/vehicle_reading.dart';

/// Clean list tile rendering a vehicle reading timestamp, ID, and inference state.
class ReadingTile extends StatelessWidget {
  final VehicleReading reading;

  const ReadingTile({super.key, required this.reading});

  @override
  Widget build(BuildContext context) {
    final isParked = reading.isParked;
    final stateColor = isParked ? AppColors.stateParked : AppColors.stateMoving;
    final timeFormatted = DateFormat('HH:mm:ss').format(reading.timestamp);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.surfaceElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.surfaceBorder),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: stateColor.withAlpha(25),
              shape: BoxShape.circle,
            ),
            child: Icon(
              isParked ? Icons.local_parking_rounded : Icons.directions_car_rounded,
              color: stateColor,
              size: 16,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      reading.vehicleId,
                      style: AppTypography.titleMedium.copyWith(fontSize: 14),
                    ),
                    Text(
                      timeFormatted,
                      style: AppTypography.labelSmall,
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      'State: ${reading.predictedState.toUpperCase()}',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: stateColor,
                      ),
                    ),
                    if (reading.confidence != null) ...[
                      const SizedBox(width: 8),
                      Text(
                        '(${(reading.confidence! * 100).toStringAsFixed(1)}% conf)',
                        style: AppTypography.labelSmall,
                      ),
                    ],
                    if (reading.gpsSpeed != null) ...[
                      const Spacer(),
                      Text(
                        '${reading.gpsSpeed!.toStringAsFixed(1)} m/s',
                        style: AppTypography.numericSub,
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
