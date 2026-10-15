/// Helper to convert technical zone IDs to friendly, human-readable names
class ZoneNameHelper {
  const ZoneNameHelper._();

  /// Map of zone_id patterns to friendly display names
  static const Map<String, String> _zoneDisplayNames = {
    'zone_1_1': 'West Roadside',
    'zone_1_2': 'West Plaza',
    'zone_1_3': 'West Market Street',
    'zone_2_1': 'Central Parking Lot',
    'zone_2_2': 'Central Market Area',
    'zone_2_3': 'Central Business District',
    'zone_3_1': 'East Riverside',
    'zone_3_2': 'North Parking Lot',
    'zone_3_3': 'East Commercial Zone',
    'zone_4_1': 'South Residential',
    'zone_4_2': 'South Shopping Plaza',
    'zone_4_3': 'South Industrial Area',
  };

  /// Get a friendly name for a zone, falling back to the original name if provided,
  /// or a formatted version of the zone_id if no mapping exists
  static String getFriendlyName(String zoneId, String? originalName) {
    // If backend provides a name, use it
    if (originalName != null && originalName.isNotEmpty) {
      return originalName;
    }

    // Check our mapping
    if (_zoneDisplayNames.containsKey(zoneId)) {
      return _zoneDisplayNames[zoneId]!;
    }

    // Fallback: format zone_X_Y -> "Zone X-Y"
    if (zoneId.startsWith('zone_')) {
      final parts = zoneId.substring(5).split('_');
      if (parts.length == 2) {
        return 'Zone ${parts[0]}-${parts[1]}';
      }
    }

    return zoneId; // Last resort
  }
}
