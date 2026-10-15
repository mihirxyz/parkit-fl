import 'package:flutter/foundation.dart';
import '../models/fl_metrics.dart';
import '../services/api_service.dart';

enum FLStateStatus { initial, loading, success, error }

/// State provider for Federated Learning convergence stats and evaluation comparisons.
class FLMetricsProvider extends ChangeNotifier {
  final ApiService _apiService;

  FLStateStatus _status = FLStateStatus.initial;
  FLMetrics? _metrics;
  String? _errorMessage;
  int _selectedRoundIndex = 9; // Default to terminal round

  FLMetricsProvider({ApiService? apiService})
      : _apiService = apiService ?? ApiService();

  FLStateStatus get status => _status;
  FLMetrics? get metrics => _metrics;
  String? get errorMessage => _errorMessage;
  int get selectedRoundIndex => _selectedRoundIndex;

  bool get isLoading => _status == FLStateStatus.loading;
  bool get hasError => _status == FLStateStatus.error;

  FLRoundMetric? get selectedRound {
    if (_metrics == null || _metrics!.history.isEmpty) return null;
    if (_selectedRoundIndex >= 0 && _selectedRoundIndex < _metrics!.history.length) {
      return _metrics!.history[_selectedRoundIndex];
    }
    return _metrics!.history.last;
  }

  void selectRound(int index) {
    if (_metrics != null && index >= 0 && index < _metrics!.history.length) {
      _selectedRoundIndex = index;
      notifyListeners();
    }
  }

  /// Fetch FL metrics from backend
  Future<void> fetchMetrics({bool silent = false}) async {
    if (!silent) {
      _status = FLStateStatus.loading;
      _errorMessage = null;
      notifyListeners();
    }

    try {
      final fetched = await _apiService.fetchFLMetrics();
      _metrics = fetched;
      _status = FLStateStatus.success;
      _errorMessage = null;
      if (fetched.history.isNotEmpty) {
        _selectedRoundIndex = fetched.history.length - 1;
      }
    } catch (e) {
      _status = FLStateStatus.error;
      _errorMessage = e.toString();
    } finally {
      notifyListeners();
    }
  }
}
