/// Represents a single vehicle telemetry observation and ML inference result.
class VehicleReading {
  final int? id;
  final String vehicleId;
  final DateTime timestamp;
  final double lat;
  final double lon;
  final String predictedState; // 'parked' or 'moving'
  final double? confidence;
  final String? zoneId;
  final double? gpsSpeed;
  final double? bleRssi;
  final double? imuMagnitude;

  const VehicleReading({
    this.id,
    required this.vehicleId,
    required this.timestamp,
    required this.lat,
    required this.lon,
    required this.predictedState,
    this.confidence,
    this.zoneId,
    this.gpsSpeed,
    this.bleRssi,
    this.imuMagnitude,
  });

  bool get isParked => predictedState.toLowerCase() == 'parked';

  factory VehicleReading.fromJson(Map<String, dynamic> json) {
    DateTime parsedDate;
    if (json['timestamp'] is String) {
      parsedDate = DateTime.tryParse(json['timestamp'] as String) ?? DateTime.now();
    } else {
      parsedDate = DateTime.now();
    }

    return VehicleReading(
      id: json['id'] as int?,
      vehicleId: json['vehicle_id'] as String? ?? 'unknown',
      timestamp: parsedDate,
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      predictedState: json['predicted_state'] as String? ?? 'moving',
      confidence: (json['confidence'] as num?)?.toDouble(),
      zoneId: json['zone_id'] as String?,
      gpsSpeed: (json['gps_speed'] as num?)?.toDouble(),
      bleRssi: (json['ble_rssi'] as num?)?.toDouble(),
      imuMagnitude: (json['imu_magnitude'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'vehicle_id': vehicleId,
        'lat': lat,
        'lon': lon,
        if (gpsSpeed != null) 'gps_speed': gpsSpeed,
        if (bleRssi != null) 'ble_rssi': bleRssi,
        if (imuMagnitude != null) 'imu_magnitude': imuMagnitude,
      };
}
