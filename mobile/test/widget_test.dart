import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkit_mobile/main.dart';
import 'package:parkit_mobile/widgets/cards/metric_stat_card.dart';
import 'package:parkit_mobile/widgets/charts/occupancy_radial_gauge.dart';

void main() {
  testWidgets('ParkItApp loads with navigation bar and map shell', (WidgetTester tester) async {
    await tester.pumpWidget(const ParkItApp());

    // Verify presence of navigation items
    expect(find.byType(BottomNavigationBar), findsOneWidget);
    expect(find.text('Live Grid'), findsOneWidget);
    expect(find.text('FL Analytics'), findsOneWidget);
  });

  testWidgets('MetricStatCard renders title, value, and accent icon', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: MetricStatCard(
            title: 'Free Spots',
            value: '42',
            icon: Icons.local_parking_rounded,
          ),
        ),
      ),
    );

    expect(find.text('Free Spots'), findsOneWidget);
    expect(find.text('42'), findsOneWidget);
    expect(find.byIcon(Icons.local_parking_rounded), findsOneWidget);
  });

  testWidgets('OccupancyRadialGauge renders occupancy percentage', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: OccupancyRadialGauge(
            occupancyRate: 0.75,
            parked: 15,
            total: 20,
          ),
        ),
      ),
    );

    expect(find.text('75%'), findsOneWidget);
    expect(find.text('15 / 20'), findsOneWidget);
    expect(find.text('Occupied'), findsOneWidget);
  });
}

