/**
 * Geospatial utility functions for collision detection
 */

/**
 * Haversine formula for accurate distance calculation on earth
 * Returns: distance in meters
 */
export function haversineDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000; // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Calculate bounding box for spatial queries
 * Returns: { minLat, maxLat, minLon, maxLon }
 */
export function calculateBoundingBox(
  lat: number,
  lon: number,
  radiusMeters: number
): { minLat: number; maxLat: number; minLon: number; maxLon: number } {
  const latChange = (radiusMeters / 111320) * 1.0; // 1 degree latitude ~= 111.32 km
  const lonChange = (radiusMeters / (111320 * Math.cos((lat * Math.PI) / 180))) * 1.0;

  return {
    minLat: lat - latChange,
    maxLat: lat + latChange,
    minLon: lon - lonChange,
    maxLon: lon + lonChange,
  };
}

/**
 * Check if point is within radius
 */
export function isWithinRadius(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
  radiusMeters: number
): boolean {
  const distance = haversineDistance(lat1, lon1, lat2, lon2);
  return distance <= radiusMeters;
}

/**
 * Create normalized collision key (always sorted for consistency)
 */
export function makeCollisionKey(circle1Id: string, circle2Id: string): string {
  return [circle1Id, circle2Id].sort().join(':');
}

/**
 * Create normalized user pair key (always sorted for consistency)
 */
export function makeUserPairKey(user1Id: string, user2Id: string): string {
  return [user1Id, user2Id].sort().join(':');
}

/**
 * Parse normalized collision key back to individual IDs
 */
export function parseCollisionKey(key: string): [string, string] {
  const parts = key.split(':');
  if (parts.length < 2 || parts[0] === undefined || parts[1] === undefined) {
    throw new Error(`Invalid collision key: ${key}`);
  }
  return [parts[0], parts[1]];
}
