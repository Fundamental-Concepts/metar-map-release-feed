# METAR Map Release Feed

The latest stable release contains the public OTA firmware and manifest.
The dashboard and device firmware source remain in the private MetarMap repository.

The sectional workflow builds a separate chart prerelease once per FAA 56-day
cycle. Its renderer uses public FAA map tiles and publishes a regional AVIF
and SHA-256 manifest. Chart prereleases never become the latest OTA release.
