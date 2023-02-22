import struct

from itertools import chain

from shapely.wkb import dumps
from shapely import from_wkt as s_from_wkt
from parsewkt import from_wkt as p_from_wkt


def geometry_formatter(val):
    if ";" in val:
        srid, wkt = val.split(';')
        srid = int(srid.split('=')[-1])
    else:
        srid = None
        wkt = val
    try:
        parsed_wkt = p_from_wkt(wkt)
        if parsed_wkt['type'] == 'GeometryCollection':
            ewkb = convert_geometrycollection_wkt_to_wkb(parsed_wkt['geometries'], srid)
        else:
            ewkb = convert_wkt_by_geom_type(parsed_wkt['coordinates'], parsed_wkt['type'], srid)
    except Exception:
        print("Unable to parse WKT using parsewkt: %s" % wkt)
        ewkb = None

    # using Shapely as fallback
    if not ewkb:
        ewkb = dumps(s_from_wkt(wkt), srid=srid)

    return ('i%ss' % len(ewkb), (len(ewkb), ewkb))


def convert_wkt_by_geom_type(coords: tuple, geom_type: str, srid: int = None):
    if geom_type == 'Point':
        return convert_point_wkt_to_wkb(coords, srid)
    elif geom_type == 'LineString':
        return convert_linestring_wkt_to_wkb(coords, srid)
    elif geom_type == 'Polygon':
        return convert_polygon_wkt_to_wkb(coords, srid)
    elif geom_type == 'MultiPoint':
        # MultiPoint parsing not yet fully functional
        # return convert_multipoint_wkt_to_wkb(coords, srid)
        return
    elif geom_type == 'MultiLineString':
        return convert_multilinestring_wkt_to_wkb(coords, srid)
    elif geom_type == 'MultiPolygon':
        return convert_multipolygon_wkt_to_wkb(coords, srid)
    else:
        return


def convert_point_wkt_to_wkb(raw_coords: tuple, srid: int = None):
    ewkb = build_ewkb_header(1)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("d" * 2, *raw_coords)  # coordinates

    return ewkb


def convert_linestring_wkt_to_wkb(raw_coords: tuple, srid: int = None):
    line_coords = list(chain.from_iterable(raw_coords))
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


def convert_polygon_wkt_to_wkb(raw_coords: tuple, srid: int = None):
    rings_cnt = len(raw_coords)
    ewkb = build_ewkb_header(3)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", rings_cnt)  # number of rings
    for raw_ring in raw_coords:
        ring_coords = list(chain.from_iterable(raw_ring))
        coords_cnt = len(ring_coords)
        points_cnt = int(coords_cnt / 2)
        ewkb += struct.pack("i", points_cnt) + struct.pack("d" * coords_cnt, *ring_coords)

    return ewkb


def convert_multipoint_wkt_to_wkb(raw_coords: str, srid: int = None):
    points_cnt = len(raw_coords)
    ewkb = build_ewkb_header(4)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", points_cnt)  # number of points
    for raw_point in raw_coords:
        ewkb += convert_point_wkt_to_wkb(raw_point)

    return ewkb


def convert_multilinestring_wkt_to_wkb(raw_coords: tuple, srid: int = None):
    lines_cnt = len(raw_coords)
    ewkb = build_ewkb_header(5)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", lines_cnt)  # number of lines
    for raw_line in raw_coords:
        ewkb += convert_linestring_wkt_to_wkb(raw_line)

    return ewkb


def convert_multipolygon_wkt_to_wkb(raw_coords: tuple, srid: int = None):
    polygons_cnt = len(raw_coords)
    ewkb = build_ewkb_header(6)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why
    ewkb += struct.pack("i", polygons_cnt)  # number of polygons
    for raw_polygon in raw_coords:
        ewkb += convert_polygon_wkt_to_wkb(raw_polygon)

    return ewkb


def convert_geometrycollection_wkt_to_wkb(raw_geoms: tuple, srid: int = None):
    ewkb = build_ewkb_header(7)
    if srid:
        ewkb += b' ' + struct.pack("i", srid)  # SRID
    else:
        ewkb += struct.pack("b", 0)  # zero byte padding, not sure why

    sub_geoms = list()

    for raw_geom in raw_geoms:
        if raw_geom['type'] == 'GeometryCollection':
            sub_geoms.append(convert_geometrycollection_wkt_to_wkb(raw_geom['geometries']))
        else:
            sub_geoms.append(convert_wkt_by_geom_type(raw_geom['coordinates'], raw_geom['type']))

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
