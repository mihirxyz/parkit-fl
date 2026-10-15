/// Application-wide API and geospatial configuration constants.
class ApiConstants {
  // Prevent instantiation.
  const ApiConstants._();

  /// Configurable backend base URL pointing to the FastAPI gateway.
  /// Defaults to loopback localhost on standard port 8000.
  /// For Android emulator use: 'http://10.0.2.2:8000/api/v1'
  static String baseUrl = 'http://127.0.0.1:8000/api/v1';

  // HTTP Request Timeouts
  static const Duration connectTimeout = Duration(seconds: 8);
  static const Duration receiveTimeout = Duration(seconds: 10);

  // Endpoints
  static String get gridZonesUrl => '$baseUrl/grid';
  static String zoneDetailUrl(String zoneId) => '$baseUrl/grid/$zoneId';
  static String get gridInitUrl => '$baseUrl/grid/init';
  static String get vehiclesUrl => '$baseUrl/vehicles';
  static String get flMetricsUrl => '$baseUrl/fl/metrics';
  static String get healthUrl => '$baseUrl/health';

  // Geographic Center & Bounding Constants (Pune, Maharashtra, India)
  static const double puneCenterLat = 18.5204;
  static const double puneCenterLon = 73.8567;
  static const double defaultZoom = 16.5;
  static const double minZoom = 14.0;
  static const double maxZoom = 19.0;

  // Real dataset bounds
  static const double puneLatMin = 18.5185;
  static const double puneLatMax = 18.5222;
  static const double puneLonMin = 73.8548;
  static const double puneLonMax = 73.8586;
}
