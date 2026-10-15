import 'package:latlong2/latlong.dart';
import 'vehicle_reading.dart';

/// Represents a geographic parking zone partition with real-time occupancy statistics.
class ParkingZone {
  final String zoneId;
  final String? name;
  final String zoneType; // 'structured' vs 'unstructured'
  final double latMin;
  final double latMax;
  final double lonMin;
  final double lonMax;
  final int totalCapacity;
  final int parkedVehicles;
  final int movingVehicles;
  final int totalVehicles;
  final double occupancyRate;
  final List<VehicleReading> recentReadings;

  const ParkingZone({
    required this.zoneId,
    this.name,
    required this.zoneType,
    required this.latMin,
    required this.latMax,
    required this.lonMin,
    required this.lonMax,
    required this.totalCapacity,
    required this.parkedVehicles,
    required this.movingVehicles,
    required this.totalVehicles,
    required this.occupancyRate,
    this.recentReadings = const [],
  });

  bool get isStructured => zoneType.toLowerCase() == 'structured';

  /// Center point of the zone bounding box
  LatLng get center => LatLng(
        (latMin + latMax) / 2.0,
        (lonMin + lonMax) / 2.0,
      );

  /// 4 corner polygon points for flutter_map PolygonLayer
  List<LatLng> get polygonPoints => [
        LatLng(latMin, lonMin),
        LatLng(latMax, lonMin),
        LatLng(latMax, lonMax),
        LatLng(latMin, lonMax),
      ];

  int get availableSpots => (totalCapacity - parkedVehicles).clamp(0, totalCapacity);

  factory ParkingZone.fromJson(Map<String, dynamic> json) {
    var rawReadings = json['recent_readings'];
    List<VehicleReading> readingsList = [];
    if (rawReadings is List) {
      readingsList = rawReadings
          .map((r) => VehicleReading.fromJson(r as Map<String, dynamic>))
          .toList();
    }

    return ParkingZone(
      zoneId: json['zone_id'] as String,
      name: json['name'] as String?,
      zoneType: json['zone_type'] as String? ?? 'unstructured',
      latMin: (json['lat_min'] as num).toDouble(),
      latMax: (json['lat_max'] as num).toDouble(),
      lonMin: (json['lon_min'] as num).toDouble(),
      lonMax: (json['lon_max'] as num).toDouble(),
      totalCapacity: json['total_capacity'] as int? ?? 10,
      parkedVehicles: json['parked_vehicles'] as int? ?? 0,
      movingVehicles: json['moving_vehicles'] as int? ?? 0,
      totalVehicles: json['total_vehicles'] as int? ?? 0,
      occupancyRate: (json['occupancy_rate'] as num?)?.toDouble() ?? 0.0,
      recentReadings: readingsList,
    );
  }

  ParkingZone copyWith({
    String? zoneId,
    String? name,
    String? zoneType,
    double? latMin,
    double? latMax,
    double? lonMin,
    double? lonMax,
    int? totalCapacity,
    int? parkedVehicles,
    int? movingVehicles,
    int? totalVehicles,
    double? occupancyRate,
    List<VehicleReading>? recentReadings,
  }) {
    return ParkingZone(
      zoneId: zoneId ?? this.zoneId,
      name: name ?? this.name,
      zoneType: zoneType ?? this.zoneType,
      latMin: latMin ?? this.latMin,
      latMax: latMax ?? this.latMax,
      lonMin: lonMin ?? this.lonMin,
      lonMax: lonMax ?? this.lonMax,
      totalCapacity: totalCapacity ?? this.totalCapacity,
      parkedVehicles: parkedVehicles ?? this.parkedVehicles,
      movingVehicles: movingVehicles ?? this.movingVehicles,
      totalVehicles: totalVehicles ?? this.totalVehicles,
      occupancyRate: occupancyRate ?? this.occupancyRate,
      recentReadings: recentReadings ?? this.recentReadings,
    );
  }
}
