import re
import struct

from operator import methodcaller
from itertools import chain

from shapely import from_wkt
from shapely.wkb import dumps


# regular expressions...
# ... to split geometry type from coordinates
GEOM_TYPE_COORDS_REGEX = re.compile(R"([A-Z]+)\s{0,}\({1,}([0-9].+[0-9])\){1,}$")
# ... to find sub geometries in geometry collections
GEOM_TYPE_SUB_GEOM_REGEX = re.compile(R"([A-Z]+)\s{0,}\((.+)\)")
# ... to split coordinate pairs in line strings and polygons
COORDS_SPLIT_REGEX = re.compile(R",\s{0,}")
# ... to split linear rings in polygons and line strings in multilinestrings
RING_SPLIT_REGEX = re.compile(R"\),\s{0,}\(")
# ... to split polygons in multipolygons
POLYGON_SPLIT_REGEX = re.compile(R"\)\),\s{0,}\(\(")
# ... to split points in multipoints
POINT_SPLIT_REGEX = re.compile(R"\)?,\s{0,}\(?")


def geometry_formatter(val):
    if ";" in val:
        srid, wkt = val.split(';')
        srid = int(srid.split('=')[-1])
    else:
        srid = None
        wkt = val
    if wkt.startswith('GEOMETRYCOLLECTION'):
        match = re.search(GEOM_TYPE_SUB_GEOM_REGEX, wkt)
        geom_type, raw_geoms = match.group(1), match.group(2)
        ewkb = convert_geometrycollection_wkt_to_wkb(raw_geoms, srid)
    else:
        match = re.search(GEOM_TYPE_COORDS_REGEX, wkt)
        geom_type, raw_coords = match.group(1), match.group(2)
        ewkb = convert_wkt_by_geom_type(raw_coords, geom_type, srid)

    # using Shapely as fallback
    if not ewkb:
        ewkb = dumps(from_wkt(wkt), srid=srid)

    return ('i%ss' % len(ewkb), (len(ewkb), ewkb))


def convert_wkt_by_geom_type(wkt: str, geom_type: str, srid: int = None):
    if geom_type.startswith('POINT'):
        return convert_point_wkt_to_wkb(wkt, srid)
    elif geom_type.startswith('LINESTRING'):
        return convert_linestring_wkt_to_wkb(wkt, srid)
    elif geom_type.startswith('POLYGON'):
        return convert_polygon_wkt_to_wkb(wkt, srid)
    elif geom_type.startswith('MULTIPOINT'):
        return convert_multipoint_wkt_to_wkb(wkt, srid)
    elif geom_type.startswith('MULTILINESTRING'):
        return convert_multilinestring_wkt_to_wkb(wkt, srid)
    elif geom_type.startswith('MULTIPOLYGON'):
        return convert_multipolygon_wkt_to_wkb(wkt, srid)
    else:
        return


def convert_point_wkt_to_wkb(raw_coords: str, srid: int = None):
    point_coords = [float(t) for t in raw_coords.split()]
    ewkb = build_ewkb_header(1)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("d" * 2, *point_coords)  # coordinates

    return ewkb


def convert_linestring_wkt_to_wkb(raw_coords: str, srid: int = None):
    line_coords = [float(xy) for xy in list(
        chain.from_iterable(list(map(methodcaller('split'), re.split(COORDS_SPLIT_REGEX, raw_coords)))))]
    coords_cnt = len(line_coords)
    points_cnt = int(coords_cnt / 2)
    ewkb = build_ewkb_header(2)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", points_cnt)  # number of points
    ewkb += struct.pack("d" * coords_cnt, *line_coords)  # coordinates

    return ewkb


def convert_polygon_wkt_to_wkb(raw_coords: str, srid: int = None):
    raw_rings = re.split(RING_SPLIT_REGEX, raw_coords)
    rings_cnt = len(raw_rings)
    ewkb = build_ewkb_header(3)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", rings_cnt)  # number of rings
    for raw_ring in raw_rings:
        ring_coords = [float(xy) for xy in list(
            chain.from_iterable(list(map(methodcaller('split'), re.split(COORDS_SPLIT_REGEX, raw_ring)))))]
        coords_cnt = len(ring_coords)
        points_cnt = int(coords_cnt / 2)
        ewkb += struct.pack("i", points_cnt) + struct.pack("d" * coords_cnt, *ring_coords)

    return ewkb


def convert_multipoint_wkt_to_wkb(raw_coords: str, srid: int = None):
    raw_points = re.split(POINT_SPLIT_REGEX, raw_coords)
    points_cnt = len(raw_points)
    ewkb = build_ewkb_header(4)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", points_cnt)  # number of points
    for raw_point in raw_points:
        ewkb += convert_point_wkt_to_wkb(raw_point)

    return ewkb


def convert_multilinestring_wkt_to_wkb(raw_coords: str, srid: int = None):
    raw_lines = re.split(RING_SPLIT_REGEX, raw_coords)
    lines_cnt = len(raw_lines)
    ewkb = build_ewkb_header(5)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", lines_cnt)  # number of lines
    for raw_line in raw_lines:
        ewkb += convert_linestring_wkt_to_wkb(raw_line)

    return ewkb


def convert_multipolygon_wkt_to_wkb(raw_coords: str, srid: int = None):
    raw_polygons = re.split(POLYGON_SPLIT_REGEX, raw_coords)
    polygons_cnt = len(raw_polygons)
    ewkb = build_ewkb_header(6)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", polygons_cnt)  # number of polygons
    for raw_polygon in raw_polygons:
        ewkb += convert_polygon_wkt_to_wkb(raw_polygon)

    return ewkb


def convert_geometrycollection_wkt_to_wkb(raw_geoms: str, srid: int = None):

    print("raw_geoms:", (raw_geoms))

    ewkb = build_ewkb_header(7)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why

    sub_geoms = list()

    subs = re.split(R",\s?[A-Z]", raw_geoms)
    while len(subs) > 1:
        if raw_geoms.startswith("GEOMETRYCOLLECTION"):
            subs = list()
            match = re.search(GEOM_TYPE_SUB_GEOM_REGEX, raw_geoms)
            _, raw_geoms = match.group(1), match.group(2)
            sub_geoms.append(convert_geometrycollection_wkt_to_wkb(raw_geoms))
        else:
            subs = re.split(R",\s?[A-Z]", raw_geoms)
            print(subs[0])
            match = re.search(GEOM_TYPE_COORDS_REGEX, subs[0])
            sub_geom_type, sub_raw_coords = match.group(1), match.group(2)
            sub_geoms.append(convert_wkt_by_geom_type(sub_raw_coords, sub_geom_type))
            raw_geoms = raw_geoms.replace(subs[0] + ",", "", 1).strip()
            print("updated raw geoms:", raw_geoms)

    ewkb += struct.pack("i", len(sub_geoms))  # number of sub geometries
    for sub_geom in sub_geoms:
        ewkb += sub_geom

    return ewkb


def build_ewkb_header(geom_type: int):
    return (
        struct.pack("b", 1) +  # endian flag
        struct.pack("b", geom_type) +  # geometry type
        struct.pack("h", 0)  # spacer
    )
