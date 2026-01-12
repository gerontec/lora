#!/usr/bin/env python3
"""
LoRa Viewshed & Coverage Analyzer
Für Berggipfel-Repeater Planung

Nutzt:
- SRTM Höhendaten (automatischer Download)
- Viewshed Berechnung (Line-of-Sight)
- Coverage Map Visualisierung

Installation:
    pip3 install srtm.py matplotlib folium

Usage:
    ./lora_viewshed.py --lat 47.669826 --lon 11.531724 --height 1310 --radius 30
"""

import argparse
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

try:
    import srtm
    SRTM_AVAILABLE = True
except ImportError:
    SRTM_AVAILABLE = False
    print("⚠️  srtm.py nicht installiert!")
    print("   Installation: pip3 install srtm.py")

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("⚠️  folium nicht installiert (optional für interaktive Karten)")
    print("   Installation: pip3 install folium")


class LoRaViewshed:
    """Viewshed Analyse für LoRa Coverage"""

    def __init__(self, tx_lat, tx_lon, tx_height, radius_km=30):
        self.tx_lat = tx_lat
        self.tx_lon = tx_lon
        self.tx_height = tx_height
        self.radius_km = radius_km

        # SRTM Daten
        if SRTM_AVAILABLE:
            self.elevation_data = srtm.get_data()
        else:
            self.elevation_data = None

    def get_elevation(self, lat, lon):
        """Hole Höhe für Koordinaten (SRTM)"""
        if self.elevation_data:
            elev = self.elevation_data.get_elevation(lat, lon)
            return elev if elev else 0
        return 0

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Berechne Distanz in km"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def line_of_sight(self, rx_lat, rx_lon, rx_height=2):
        """
        Check Line-of-Sight zwischen TX und RX

        Returns:
            bool: True wenn sichtbar
            float: Clearance in Metern (positiv = frei, negativ = blockiert)
        """
        if not self.elevation_data:
            # Ohne SRTM Daten: Optimistische Annahme
            return True, 100.0

        # TX Höhe über Meer
        tx_ground = self.get_elevation(self.tx_lat, self.tx_lon)
        tx_asl = tx_ground + self.tx_height

        # RX Höhe über Meer
        rx_ground = self.get_elevation(rx_lat, rx_lon)
        rx_asl = rx_ground + rx_height

        # Distanz
        distance = self.haversine_distance(self.tx_lat, self.tx_lon, rx_lat, rx_lon)

        # Sample Punkte entlang der Linie
        num_samples = max(10, int(distance * 10))  # 10 Samples pro km

        min_clearance = float('inf')

        for i in range(1, num_samples):
            # Interpoliere Position
            t = i / num_samples
            lat = self.tx_lat + t * (rx_lat - self.tx_lat)
            lon = self.tx_lon + t * (rx_lon - self.tx_lon)

            # Höhe an dieser Position
            ground = self.get_elevation(lat, lon)

            # Erwartete Strahl-Höhe (linear zwischen TX und RX)
            beam_height = tx_asl + t * (rx_asl - tx_asl)

            # Clearance (mit Earth Curvature)
            earth_curve = (distance * 1000 * t * (1-t)) / 12.74  # in Metern
            clearance = beam_height - ground - earth_curve

            # Fresnel Zone (60% für praktische Clearance)
            wavelength = 0.345  # 868 MHz: λ ≈ 34.5 cm
            dist_km = distance * t
            fresnel = 0.6 * 8.656 * np.sqrt((dist_km * (distance - dist_km)) / distance)

            clearance -= fresnel

            if clearance < min_clearance:
                min_clearance = clearance

        return (min_clearance > 0), min_clearance

    def calculate_coverage(self, resolution=100):
        """
        Berechne Coverage Map

        Args:
            resolution: Grid Auflösung (100 = 100x100 Punkte)

        Returns:
            dict: Coverage Daten
        """
        print(f"Berechne Coverage für {self.tx_lat}, {self.tx_lon} (Höhe: {self.tx_height}m)")
        print(f"Radius: {self.radius_km} km")
        print(f"Auflösung: {resolution}x{resolution}")

        # Grid erstellen
        # 1° Latitude ≈ 111 km
        # 1° Longitude ≈ 71 km (bei 47°N)
        lat_range = self.radius_km / 111
        lon_range = self.radius_km / 71

        lats = np.linspace(self.tx_lat - lat_range, self.tx_lat + lat_range, resolution)
        lons = np.linspace(self.tx_lon - lon_range, self.tx_lon + lon_range, resolution)

        coverage = np.zeros((resolution, resolution))
        clearance_map = np.zeros((resolution, resolution))

        total = resolution * resolution
        count = 0

        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                count += 1
                if count % 500 == 0:
                    print(f"  Fortschritt: {count}/{total} ({100*count/total:.1f}%)")

                # Distanz check
                dist = self.haversine_distance(self.tx_lat, self.tx_lon, lat, lon)
                if dist > self.radius_km:
                    coverage[i, j] = -1  # Out of range
                    continue

                # Line-of-Sight
                visible, clearance = self.line_of_sight(lat, lon)

                coverage[i, j] = 1 if visible else 0
                clearance_map[i, j] = clearance

        print("  Fertig!")

        return {
            'lats': lats,
            'lons': lons,
            'coverage': coverage,
            'clearance': clearance_map
        }

    def plot_coverage(self, coverage_data, output_file='lora_coverage.png'):
        """Visualisiere Coverage Map"""

        lats = coverage_data['lats']
        lons = coverage_data['lons']
        coverage = coverage_data['coverage']

        fig, ax = plt.subplots(figsize=(12, 10))

        # Custom Colormap: Rot=blockiert, Grün=sichtbar, Grau=out of range
        colors = ['gray', 'red', 'green']
        n_bins = 3
        cmap = LinearSegmentedColormap.from_list('coverage', colors, N=n_bins)

        # Plot
        im = ax.contourf(lons, lats, coverage, levels=[-1.5, -0.5, 0.5, 1.5], cmap=cmap)

        # TX Punkt
        ax.plot(self.tx_lon, self.tx_lat, 'y*', markersize=20, label=f'TX ({self.tx_height}m)')

        # Grid
        ax.grid(True, alpha=0.3)

        # Labels
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title(f'LoRa Coverage: {self.tx_lat:.4f}, {self.tx_lon:.4f} @ {self.tx_height}m\nRadius: {self.radius_km} km')

        # Legend
        ax.legend()

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, ticks=[-1, 0, 1])
        cbar.ax.set_yticklabels(['Out of Range', 'Blocked', 'Visible'])

        plt.tight_layout()
        plt.savefig(output_file, dpi=150)
        print(f"✓ Coverage Map gespeichert: {output_file}")

        plt.show()

    def export_kml(self, coverage_data, output_file='lora_coverage.kml'):
        """Exportiere als KML für Google Earth"""

        lats = coverage_data['lats']
        lons = coverage_data['lons']
        coverage = coverage_data['coverage']

        with open(output_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            f.write('  <Document>\n')
            f.write(f'    <name>LoRa Coverage {self.tx_lat}, {self.tx_lon}</name>\n')

            # TX Point
            f.write('    <Placemark>\n')
            f.write('      <name>TX Station</name>\n')
            f.write('      <Point>\n')
            f.write(f'        <coordinates>{self.tx_lon},{self.tx_lat},{self.tx_height}</coordinates>\n')
            f.write('      </Point>\n')
            f.write('    </Placemark>\n')

            # Coverage Polygons (vereinfacht)
            # TODO: Vollständige Polygon-Generierung

            f.write('  </Document>\n')
            f.write('</kml>\n')

        print(f"✓ KML exportiert: {output_file}")

    def export_html(self, coverage_data, output_file='lora_coverage.html'):
        """Exportiere interaktive HTML Karte (Folium)"""

        if not FOLIUM_AVAILABLE:
            print("⚠️  folium nicht verfügbar, HTML Export übersprungen")
            return

        lats = coverage_data['lats']
        lons = coverage_data['lons']
        coverage = coverage_data['coverage']

        # Erstelle Folium Map
        m = folium.Map(location=[self.tx_lat, self.tx_lon], zoom_start=12)

        # TX Marker
        folium.Marker(
            [self.tx_lat, self.tx_lon],
            popup=f'TX: {self.tx_height}m',
            icon=folium.Icon(color='red', icon='signal')
        ).add_to(m)

        # Coverage Overlay (vereinfacht als Kreise)
        # TODO: Heatmap oder Polygone

        m.save(output_file)
        print(f"✓ HTML Map gespeichert: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='LoRa Viewshed & Coverage Analyzer für Berggipfel'
    )
    parser.add_argument('--lat', type=float, required=True, help='TX Latitude')
    parser.add_argument('--lon', type=float, required=True, help='TX Longitude')
    parser.add_argument('--height', type=float, required=True, help='TX Höhe (m über Grund)')
    parser.add_argument('--radius', type=float, default=30, help='Coverage Radius (km)')
    parser.add_argument('--resolution', type=int, default=50, help='Grid Resolution')
    parser.add_argument('--output', default='lora_coverage', help='Output Filename (ohne Extension)')

    args = parser.parse_args()

    # Check SRTM
    if not SRTM_AVAILABLE:
        print("\n⚠️  CRITICAL: srtm.py nicht installiert!")
        print("   Ohne SRTM Daten kann keine Viewshed-Analyse durchgeführt werden.")
        print("\n   Installation:")
        print("   pip3 install srtm.py matplotlib")
        sys.exit(1)

    # Erstelle Analyzer
    analyzer = LoRaViewshed(args.lat, args.lon, args.height, args.radius)

    # Berechne Coverage
    coverage = analyzer.calculate_coverage(resolution=args.resolution)

    # Visualisiere
    analyzer.plot_coverage(coverage, output_file=f"{args.output}.png")

    # Export
    # analyzer.export_kml(coverage, output_file=f"{args.output}.kml")
    # analyzer.export_html(coverage, output_file=f"{args.output}.html")

    # Statistik
    visible = np.sum(coverage['coverage'] == 1)
    blocked = np.sum(coverage['coverage'] == 0)
    total = visible + blocked

    print(f"\n{'='*50}")
    print(f"Coverage Statistik:")
    print(f"  Sichtbar:  {visible}/{total} ({100*visible/total:.1f}%)")
    print(f"  Blockiert: {blocked}/{total} ({100*blocked/total:.1f}%)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
