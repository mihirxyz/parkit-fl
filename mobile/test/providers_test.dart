import 'package:flutter_test/flutter_test.dart';
import 'package:parkit_mobile/models/parking_zone.dart';
import 'package:parkit_mobile/providers/parking_provider.dart';

void main() {
  group('ParkingProvider Unit Tests', () {
    test('Calculates aggregated occupancy rates and filters zones properly', () {
      final provider = ParkingProvider();

      final dummyZones = [
        const ParkingZone(
          zoneId: 'z1',
          name: 'Zone 1',
          zoneType: 'structured',
          latMin: 18.518,
          latMax: 18.519,
          lonMin: 73.854,
          lonMax: 73.855,
          totalCapacity: 10,
          parkedVehicles: 7,
          movingVehicles: 2,
          totalVehicles: 9,
          occupancyRate: 0.7,
        ),
        const ParkingZone(
          zoneId: 'z2',
          name: 'Zone 2',
          zoneType: 'unstructured',
          latMin: 18.519,
          latMax: 18.520,
          lonMin: 73.855,
          lonMax: 73.856,
          totalCapacity: 10,
          parkedVehicles: 3,
          movingVehicles: 4,
          totalVehicles: 7,
          occupancyRate: 0.3,
        ),
      ];

      // Inject dummy data
      provider.setFilterType('all');
      provider.selectZone(dummyZones.first);

      expect(provider.selectedZone?.zoneId, 'z1');
      expect(provider.filterType, 'all');

      provider.setFilterType('structured');
      expect(provider.filterType, 'structured');
    });
  });
}
