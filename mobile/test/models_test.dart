import 'package:flutter_test/flutter_test.dart';
import 'package:parkit_mobile/models/fl_metrics.dart';
import 'package:parkit_mobile/models/parking_zone.dart';
import 'package:parkit_mobile/models/vehicle_reading.dart';

void main() {
  group('ParkingZone Model Tests', () {
    test('Correctly parses ParkingZone from JSON and computes polygon bounds', () {
      final json = {
        'zone_id': 'zone_0_0',
        'name': 'Zone A (North-West)',
        'zone_type': 'structured',
        'lat_min': 18.5210,
        'lat_max': 18.5222,
        'lon_min': 73.8548,
        'lon_max': 73.8561,
        'total_capacity': 20,
        'parked_vehicles': 14,
        'moving_vehicles': 3,
        'total_vehicles': 17,
        'occupancy_rate': 0.70,
        'recent_readings': [
          {
            'vehicle_id': 'VH_101',
            'timestamp': '2026-09-24T12:00:00Z',
            'lat': 18.5215,
            'lon': 73.8550,
            'predicted_state': 'parked',
            'confidence': 0.995,
            'zone_id': 'zone_0_0',
          }
        ],
      };

      final zone = ParkingZone.fromJson(json);

      expect(zone.zoneId, 'zone_0_0');
      expect(zone.name, 'Zone A (North-West)');
      expect(zone.isStructured, isTrue);
      expect(zone.totalCapacity, 20);
      expect(zone.parkedVehicles, 14);
      expect(zone.availableSpots, 6);
      expect(zone.occupancyRate, 0.70);
      expect(zone.polygonPoints.length, 4);
      expect(zone.recentReadings.length, 1);
      expect(zone.recentReadings.first.vehicleId, 'VH_101');
      expect(zone.recentReadings.first.isParked, isTrue);
    });
  });

  group('VehicleReading Model Tests', () {
    test('Serializes to JSON accurately for backend ingestion', () {
      final reading = VehicleReading(
        vehicleId: 'test_veh_99',
        timestamp: DateTime(2026, 9, 24, 10, 0, 0),
        lat: 18.5204,
        lon: 73.8567,
        gpsSpeed: 0.0,
        bleRssi: -50.0,
        imuMagnitude: 9.81,
        predictedState: 'parked',
      );

      final json = reading.toJson();
      expect(json['vehicle_id'], 'test_veh_99');
      expect(json['lat'], 18.5204);
      expect(json['lon'], 73.8567);
      expect(json['gps_speed'], 0.0);
      expect(json['ble_rssi'], -50.0);
    });
  });

  group('FLMetrics Model Tests', () {
    test('Parses FL experiment history, baseline, and round details', () {
      final json = {
        'experiment': {
          'type': 'federated_learning',
          'num_clients': 5,
          'num_rounds': 10,
          'local_epochs': 3,
          'duration_seconds': 87.9,
        },
        'global_model_history': [
          {
            'round': 1,
            'accuracy': 0.925,
            'precision_macro': 0.910,
            'recall_macro': 0.905,
            'f1_macro': 0.907,
            'precision_moving': 0.93,
            'recall_moving': 0.92,
            'f1_moving': 0.925,
            'precision_parked': 0.90,
            'recall_parked': 0.89,
            'f1_parked': 0.895,
          },
          {
            'round': 10,
            'accuracy': 0.9947,
            'precision_macro': 0.9935,
            'recall_macro': 0.9902,
            'f1_macro': 0.9918,
            'precision_moving': 0.9964,
            'recall_moving': 0.9940,
            'f1_moving': 0.9952,
            'precision_parked': 0.9900,
            'recall_parked': 0.9850,
            'f1_parked': 0.9875,
          }
        ],
        'centralized_baseline': {
          'test_accuracy': 0.9947,
          'test_f1': 0.9933,
          'test_precision': 0.9964,
          'test_recall': 0.9902,
        },
      };

      final flMetrics = FLMetrics.fromJson(json);

      expect(flMetrics.experiment.numClients, 5);
      expect(flMetrics.experiment.numRounds, 10);
      expect(flMetrics.history.length, 2);
      expect(flMetrics.history.last.accuracy, 0.9947);
      expect(flMetrics.centralizedBaseline?.testAccuracy, 0.9947);
    });
  });
}
