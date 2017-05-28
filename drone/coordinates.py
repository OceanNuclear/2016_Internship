from math import pi, log, tan, radians, degrees, exp, atan, atan2
from collections import namedtuple
from numpy import sin, cos, sqrt


RADIUS_EARTH = 6378137
INV_F =  298.257224
F = 1 / INV_F
ONE_MIN_F_SQ = (1 - F) ** 2


LLA = namedtuple("LLA", "lat long alt")
LatLong = namedtuple("LatLong", "lat long")
TileCoord = namedtuple("TileIndex", "x y")
MapCoord = namedtuple("MapCoord", "x y")
PxCoord = namedtuple("PxCoord", "x y")


def ecef_to_enu(lat, lon, x0, y0, z0, x, y, z):
    dx = x - x0
    dy = y - y0
    dz = z - z0

    x = dx*-sin(lon) + dy*cos(lon)
    y = dx*-sin(lat)*cos(lon) + dy*-sin(lat)*sin(lon) + dz*cos(lat)
    z = dx*cos(lat)*cos(lon) + dy*cos(lat)*sin(lon) + dz*sin(lat)

    return x, y, z


def lla_to_ecef(lat, lon, alt):
    c = 1 / sqrt(cos(lat) ** 2 + ONE_MIN_F_SQ * sin(lat) ** 2)
    s = ONE_MIN_F_SQ * c

    x = (RADIUS_EARTH * c + alt) * cos(lat) * cos(lon)
    y = (RADIUS_EARTH * c + alt) * cos(lat) * sin(lon)
    z = (RADIUS_EARTH * s + alt) * sin(lat)

    return x, y, z


class LatLong:

    def __init__(self, lat, long):
        self.lat = lat
        self.long = long

    def haversine_dist(self, other):
        dlat = radians(other.lat - self.lat)
        dlong = radians(other.long - self.long)

        a = sin(dlat/2) ** 2 + cos(self.lat) * cos(other.lat) * sin(dlong/2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return RADIUS_EARTH * c


class WGS84CoordinateSystem:

    def __init__(self, zoom, tile_size=256):
        self._tile_size = tile_size
        self._zoom = zoom

    @property
    def zoom(self):
        return self._zoom

    @property
    def tile_size(self):
        return self._tile_size

    def lat_long_to_map(self, lat_long):
        lat = radians(lat_long.lat)
        long = radians(lat_long.long)

        x = self._tile_size * (0.5 + long / (2*pi))
        y = self._tile_size * (0.5 - log(tan(pi/4 + lat/2))/(2*pi))

        return MapCoord(x, y)

    def map_to_lat_long(self, map):
        lat_rad = 2 * (pi/4 - atan(exp(pi - (2 * pi * map.y)/self._tile_size)))
        long_rad = pi - (2 * pi * map.x) / self._tile_size
        lat = degrees(lat_rad)
        long =- degrees(long_rad)

        return LatLong(lat, long)

    def map_to_px(self, map):
        z = 2 ** self._zoom
        return PxCoord(map.x * z, map.y * z)

    def px_to_map(self, px):
        z = 2 ** self._zoom
        return MapCoord(px.x / z, px.y / z)

    def map_to_tile(self, map):
        z = 2 ** self._zoom

        # Floor div
        tx = int((map.x * z) / self._tile_size)
        ty = int((map.y * z) / self._tile_size)

        return TileCoord(tx, ty)

    def tile_to_map(self, tile):
        z = 2 ** self._zoom
        return PxCoord(tile.x * self._tile_size / z, tile.y * self._tile_size / z)
