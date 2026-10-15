/// Custom API exception class providing human-readable diagnostic messages.
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final String? url;

  const ApiException(this.message, {this.statusCode, this.url});

  @override
  String toString() {
    if (statusCode != null) {
      return 'ApiException ($statusCode): $message';
    }
    return 'ApiException: $message';
  }
}
