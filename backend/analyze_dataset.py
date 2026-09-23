#!/usr/bin/env python3
"""Analyze SUMO dataset statistics for debugging."""

import csv
import math
import sys
from collections import Counter
from pathlib import Path

def analyze_dataset(csv_path: Path) -> None:
    """Analyze label distribution and coordinate ranges."""
    if not csv_path.exists():
        print(f"Dataset not found: {csv_path}", file=sys.stderr)
        return
    
    labels = []
    lats = []
    lons = []
    
    with csv_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels.append(row['label'])
            lats.append(float(row['lat']))
            lons.append(float(row['lon']))
    
    # Label distribution
    label_counts = Counter(labels)
    total = len(labels)
    print("=" * 60)
    print("LABEL DISTRIBUTION")
    print("=" * 60)
    for label, count in sorted(label_counts.items()):
        pct = 100.0 * count / total
        print(f"{label:15} {count:6d} rows ({pct:5.1f}%)")
    print(f"{'TOTAL':15} {total:6d} rows")
    
    # Coordinate statistics
    print("\n" + "=" * 60)
    print("COORDINATE STATISTICS")
    print("=" * 60)
    
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    lat_mean = sum(lats) / len(lats)
    lon_mean = sum(lons) / len(lons)
    
    lat_std = (sum((x - lat_mean)**2 for x in lats) / len(lats))**0.5
    lon_std = (sum((x - lon_mean)**2 for x in lons) / len(lons))**0.5
    
    lat_span = lat_max - lat_min
    lon_span = lon_max - lon_min
    
    # Convert degrees to approximate metres
    meters_per_degree_lat = 111000.0
    avg_lat = (lat_min + lat_max) / 2.0
    meters_per_degree_lon = 111000.0 * math.cos(math.radians(avg_lat))
    
    lat_span_m = lat_span * meters_per_degree_lat
    lon_span_m = lon_span * meters_per_degree_lon
    
    print(f"Latitude:")
    print(f"  Min:     {lat_min:.7f}°")
    print(f"  Max:     {lat_max:.7f}°")
    print(f"  Mean:    {lat_mean:.7f}°")
    print(f"  Span:    {lat_span:.7f}° ({lat_span_m:.1f} m)")
    print(f"  Std Dev: {lat_std:.7f}°")
    
    print(f"\nLongitude:")
    print(f"  Min:     {lon_min:.7f}°")
    print(f"  Max:     {lon_max:.7f}°")
    print(f"  Mean:    {lon_mean:.7f}°")
    print(f"  Span:    {lon_span:.7f}° ({lon_span_m:.1f} m)")
    print(f"  Std Dev: {lon_std:.7f}°")
    
    print(f"\nExpected network span: ~400m x 400m")
    print(f"Actual span: {lon_span_m:.1f}m (lon) x {lat_span_m:.1f}m (lat)")
    print("=" * 60)

if __name__ == "__main__":
    csv_path = Path(__file__).parent / "app" / "ml" / "data" / "sumo_dataset.csv"
    analyze_dataset(csv_path)

