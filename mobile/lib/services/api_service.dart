import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import '../core/constants/api_constants.dart';
import '../models/fl_metrics.dart';
import '../models/parking_zone.dart';
import '../models/vehicle_reading.dart';
import 'api_exception.dart';

/// Centralized HTTP client managing all backend API communication.
class ApiService {
  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Fetch all 9 spatial grid zones with real-time occupancy counts.
  Future<List<ParkingZone>> fetchGridZones() async {
    final uri = Uri.parse(ApiConstants.gridZonesUrl);
    try {
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(ApiConstants.receiveTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> jsonList = jsonDecode(response.body);
        return jsonList
            .map((item) => ParkingZone.fromJson(item as Map<String, dynamic>))
            .toList();
      } else {
        throw ApiException(
          'Failed to load parking zones (HTTP ${response.statusCode})',
          statusCode: response.statusCode,
          url: uri.toString(),
        );
      }
    } on SocketException {
      throw ApiException(
        'Backend server is unreachable at ${ApiConstants.baseUrl}. Please ensure FastAPI is running.',
        url: uri.toString(),
      );
    } on TimeoutException {
      throw ApiException(
        'Connection timed out while fetching parking zones.',
        url: uri.toString(),
      );
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Unexpected network error: $e', url: uri.toString());
    }
  }

  /// Fetch detailed information and recent telemetry for a single zone.
  Future<ParkingZone> fetchZoneDetail(String zoneId) async {
    final uri = Uri.parse(ApiConstants.zoneDetailUrl(zoneId));
    try {
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(ApiConstants.receiveTimeout);

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonMap = jsonDecode(response.body);
        return ParkingZone.fromJson(jsonMap);
      } else {
        throw ApiException(
          'Failed to load zone detail for $zoneId',
          statusCode: response.statusCode,
          url: uri.toString(),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error fetching zone $zoneId: $e', url: uri.toString());
    }
  }

  /// Ingest a vehicle telemetry reading and receive ML classification.
  Future<VehicleReading> submitVehicleReading(VehicleReading reading) async {
    final uri = Uri.parse(ApiConstants.vehiclesUrl);
    try {
      final response = await _client
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(reading.toJson()),
          )
          .timeout(ApiConstants.receiveTimeout);

      if (response.statusCode == 201 || response.statusCode == 200) {
        final Map<String, dynamic> jsonMap = jsonDecode(response.body);
        return VehicleReading.fromJson(jsonMap);
      } else {
        throw ApiException(
          'Failed to submit telemetry reading (HTTP ${response.statusCode})',
          statusCode: response.statusCode,
          url: uri.toString(),
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error submitting vehicle reading: $e', url: uri.toString());
    }
  }

  /// Fetch Federated Learning round metrics and baseline comparison.
  Future<FLMetrics> fetchFLMetrics() async {
    final uri = Uri.parse(ApiConstants.flMetricsUrl);
    try {
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(ApiConstants.receiveTimeout);

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonMap = jsonDecode(response.body);
        return FLMetrics.fromJson(jsonMap);
      } else {
        throw ApiException(
          'Failed to load FL metrics (HTTP ${response.statusCode})',
          statusCode: response.statusCode,
          url: uri.toString(),
        );
      }
    } on SocketException {
      throw ApiException(
        'Backend server is unreachable at ${ApiConstants.baseUrl}.',
        url: uri.toString(),
      );
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error fetching FL metrics: $e', url: uri.toString());
    }
  }

  /// Check backend health.
  Future<bool> checkHealth() async {
    try {
      final uri = Uri.parse(ApiConstants.healthUrl);
      final response = await _client
          .get(uri)
          .timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
