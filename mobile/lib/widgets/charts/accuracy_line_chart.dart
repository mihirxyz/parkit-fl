import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';
import '../../models/fl_metrics.dart';

/// FL Accuracy Convergence Chart displaying FL rounds vs Centralized Baseline
/// with animated left-to-right drawing on screen load.
class AccuracyLineChart extends StatefulWidget {
  final List<FLRoundMetric> history;
  final double? centralizedBaseline;
  final int selectedRoundIndex;
  final ValueChanged<int> onRoundSelected;

  const AccuracyLineChart({
    super.key,
    required this.history,
    this.centralizedBaseline,
    required this.selectedRoundIndex,
    required this.onRoundSelected,
  });

  @override
  State<AccuracyLineChart> createState() => _AccuracyLineChartState();
}

class _AccuracyLineChartState extends State<AccuracyLineChart>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animController;
  late final Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );
    _animation = CurvedAnimation(
      parent: _animController,
      curve: Curves.easeOutCubic,
    );
    _animController.forward();
  }

  @override
  void didUpdateWidget(covariant AccuracyLineChart oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.history.length != widget.history.length) {
      _animController.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  List<FlSpot> _getAnimatedSpots(List<FlSpot> fullSpots, double progress) {
    if (fullSpots.isEmpty) return [];
    if (fullSpots.length == 1 || progress >= 1.0) return fullSpots;

    final double minX = fullSpots.first.x;
    final double maxX = fullSpots.last.x;
    final double currentMaxX = minX + (maxX - minX) * progress;

    final List<FlSpot> result = [];
    for (int i = 0; i < fullSpots.length; i++) {
      final spot = fullSpots[i];
      if (spot.x <= currentMaxX) {
        result.add(spot);
      } else {
        if (i > 0) {
          final prevSpot = fullSpots[i - 1];
          final t = (currentMaxX - prevSpot.x) / (spot.x - prevSpot.x);
          final interpolatedY = prevSpot.y + t * (spot.y - prevSpot.y);
          result.add(FlSpot(currentMaxX, interpolatedY));
        }
        break;
      }
    }
    if (result.isEmpty && fullSpots.isNotEmpty) {
      result.add(fullSpots.first);
    }
    return result;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.history.isEmpty) {
      return const SizedBox(
        height: 220,
        child: Center(child: Text('No FL training rounds available')),
      );
    }

    final fullSpots = widget.history.asMap().entries.map((e) {
      return FlSpot(e.key.toDouble() + 1, e.value.accuracy * 100);
    }).toList();

    final baselineVal = (widget.centralizedBaseline ?? 0.9947) * 100;

    return AspectRatio(
      aspectRatio: 1.7,
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, _) {
          final animatedSpots = _getAnimatedSpots(fullSpots, _animation.value);
          final baselineProgress = _animation.value;
          final double baselineMaxX =
              1.0 + (widget.history.length - 1.0) * baselineProgress;

          return LineChart(
            LineChartData(
              minX: 1,
              maxX: widget.history.length.toDouble(),
              minY: 97.0,
              maxY: 100.5,
              gridData: FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: 1.0,
                getDrawingHorizontalLine: (v) => const FlLine(
                  color: AppColors.surfaceBorder,
                  strokeWidth: 1,
                  dashArray: [4, 4],
                ),
              ),
              titlesData: FlTitlesData(
                show: true,
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 1.0,
                    reservedSize: 42,
                    getTitlesWidget: (v, m) => Text(
                      '${v.toStringAsFixed(v % 1 == 0 ? 0 : 1)}%',
                      style: AppTypography.numericSub.copyWith(fontSize: 10),
                    ),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 1,
                    getTitlesWidget: (v, m) {
                      final int r = v.toInt();
                      if (r < 1 || r > widget.history.length) {
                        return const SizedBox.shrink();
                      }
                      final isSel = (r - 1 == widget.selectedRoundIndex);
                      return Padding(
                        padding: const EdgeInsets.only(top: 8.0),
                        child: Text(
                          'R$r',
                          style: AppTypography.numericSub.copyWith(
                            fontSize: 10,
                            color: isSel ? AppColors.primary : AppColors.textMuted,
                            fontWeight: isSel ? FontWeight.bold : FontWeight.normal,
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(
                show: true,
                border: Border.all(color: AppColors.surfaceBorder),
              ),
              lineTouchData: LineTouchData(
                touchCallback: (event, response) {
                  if (response?.lineBarSpots != null &&
                      response!.lineBarSpots!.isNotEmpty) {
                    final spot = response.lineBarSpots!.first;
                    final idx = spot.x.toInt() - 1;
                    if (idx >= 0 && idx < widget.history.length) {
                      widget.onRoundSelected(idx);
                    }
                  }
                },
              ),
              lineBarsData: [
                LineChartBarData(
                  spots: animatedSpots,
                  isCurved: true,
                  curveSmoothness: 0.25,
                  color: AppColors.primary,
                  barWidth: 3,
                  isStrokeCapRound: true,
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, percent, barData, index) {
                      final isSel = (index == widget.selectedRoundIndex);
                      return FlDotCirclePainter(
                        radius: isSel ? 6 : 3.5,
                        color: isSel ? AppColors.primaryLight : AppColors.primary,
                        strokeWidth: isSel ? 3 : 1.5,
                        strokeColor: AppColors.background,
                      );
                    },
                  ),
                  belowBarData: BarAreaData(
                    show: true,
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        AppColors.primary.withAlpha(50),
                        AppColors.primary.withAlpha(0),
                      ],
                    ),
                  ),
                ),
                LineChartBarData(
                  spots: [
                    FlSpot(1, baselineVal),
                    FlSpot(baselineMaxX, baselineVal),
                  ],
                  isCurved: false,
                  color: AppColors.centralizedBaseline,
                  barWidth: 2,
                  dashArray: [6, 4],
                  dotData: const FlDotData(show: false),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
