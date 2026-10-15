import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';

/// Animated radial progress gauge visualizing occupancy percentage.
class OccupancyRadialGauge extends StatelessWidget {
  final double occupancyRate;
  final int parked;
  final int total;
  final double size;

  const OccupancyRadialGauge({
    super.key,
    required this.occupancyRate,
    required this.parked,
    required this.total,
    this.size = 140,
  });

  @override
  Widget build(BuildContext context) {
    final clampedRate = occupancyRate.clamp(0.0, 1.0);
    final color = AppColors.forOccupancy(clampedRate);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size),
            painter: _RadialGaugePainter(
              progress: clampedRate,
              color: color,
              backgroundColor: AppColors.surfaceElevated,
              strokeWidth: 12,
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${(clampedRate * 100).toInt()}%',
                style: AppTypography.numericMetric.copyWith(
                  fontSize: 26,
                  color: color,
                ),
              ),
              Text(
                '$parked / $total',
                style: AppTypography.numericSub,
              ),
              const Text(
                'Occupied',
                style: TextStyle(
                  fontSize: 10,
                  color: AppColors.textMuted,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _RadialGaugePainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color backgroundColor;
  final double strokeWidth;

  _RadialGaugePainter({
    required this.progress,
    required this.color,
    required this.backgroundColor,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Track Paint
    final bgPaint = Paint()
      ..color = backgroundColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    // Value Arc Paint
    final valPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    // Draw background full circle
    canvas.drawCircle(center, radius, bgPaint);

    // Draw active arc from top (-90 degrees)
    final sweepAngle = 2 * math.pi * progress;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2,
      sweepAngle,
      false,
      valPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _RadialGaugePainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.color != color ||
        oldDelegate.backgroundColor != backgroundColor;
  }
}
