import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'providers/fl_metrics_provider.dart';
import 'providers/parking_provider.dart';
import 'screens/main_navigation_screen.dart';
import 'services/api_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ParkItApp());
}

class ParkItApp extends StatelessWidget {
  const ParkItApp({super.key});

  @override
  Widget build(BuildContext context) {
    final apiService = ApiService();

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => ParkingProvider(apiService: apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => FLMetricsProvider(apiService: apiService),
        ),
      ],
      child: MaterialApp(
        title: 'ParkIt FL',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: const MainNavigationScreen(),
      ),
    );
  }
}

