from .test_datatypes import TypeMixin

COL_FUNCS = {'a': 'st_asewkt'}


class TestPointGeometry(TypeMixin):
    datatypes = ['geometry']
    data = [('POINT(10.1 20)',), ('POINT(30.5 40.6)',), ('SRID=4326;POINT(40.123 50.345)',)]

    def test_type(self, conn, cursor, schema_table, data, func_dict=COL_FUNCS):
        super(TestPointGeometry, self).test_type(conn, cursor, schema_table, data, func_dict)


class TestLinestringGeometry(TypeMixin):
    datatypes = ['geometry']
    data = [('LINESTRING(10 10,20 30,100.456 40)',), ('SRID=4326;LINESTRING(30 10,10 30,40.12 40.23)',)]

    def test_type(self, conn, cursor, schema_table, data, func_dict=COL_FUNCS):
        super(TestLinestringGeometry, self).test_type(conn, cursor, schema_table, data, func_dict)


class TestPolygonGeometry(TypeMixin):
    datatypes = ['geometry']
    data = [
        ('POLYGON((30 10,40 40,20 40,10 20,30 10))',),
        ('SRID=4326;POLYGON((35 10,45 45,15 40,10 20,35 10),(20 30,35 35,30 20,20 30))',)]

    def test_type(self, conn, cursor, schema_table, data, func_dict=COL_FUNCS):
        super(TestPolygonGeometry, self).test_type(conn, cursor, schema_table, data, func_dict)


class TestMultiPointGeometry(TypeMixin):
    datatypes = ['geometry']
    data = [
        ('MULTIPOINT(10 40,40 30,20 20,30 10)',),
        ('SRID=4326;MULTIPOINT(10 40,40 30,20 20,30 10)',)]

    def test_type(self, conn, cursor, schema_table, data, func_dict=COL_FUNCS):
        super(TestMultiPointGeometry, self).test_type(conn, cursor, schema_table, data, func_dict)


class TestMultiLineStringGeometry(TypeMixin):
    datatypes = ['geometry']
    data = [
        ('MULTILINESTRING((10 10,20 20,10 40),(40 40,30 30,40 20,30 10))',),
        ('SRID=4326;MULTILINESTRING((10 10,20 20,10 40),(40 40,30 30,40 20,30 10))',)]

    def test_type(self, conn, cursor, schema_table, data, func_dict=COL_FUNCS):
        super(TestMultiLineStringGeometry, self).test_type(conn, cursor, schema_table, data, func_dict)


class TestMultiPolygonGeometry(TypeMixin):
    datatypes = ['geometry']
    data = [
        ('MULTIPOLYGON(((30 20,45 40,10 40,30 20)),((15 5,40 10,10 20,5 10,15 5)))',),
        ('SRID=4326;MULTIPOLYGON(((30 20,45 40,10 40,30 20)),((15 5,40 10,10 20,5 10,15 5)))',)]

    def test_type(self, conn, cursor, schema_table, data, func_dict=COL_FUNCS):
        super(TestMultiPolygonGeometry, self).test_type(conn, cursor, schema_table, data, func_dict)


class TestGeometryCollection(TypeMixin):
    datatypes = ['geometry']
    data = [
        ('SRID=4326;GEOMETRYCOLLECTION(POINT(40 10),LINESTRING(10 10,20 20,10 40))',),
        (
            'SRID=4326;GEOMETRYCOLLECTION(GEOMETRYCOLLECTION(POINT(40 10),POINT(45 45),' +
            'LINESTRING(10 10,20 20,10 40)))',
        ),
        (
            'SRID=4326;GEOMETRYCOLLECTION(POINT(10 40),POINT(20 40))',
        ),
    ]

    def test_type(self, conn, cursor, schema_table, data, func_dict=COL_FUNCS):
        super(TestGeometryCollection, self).test_type(conn, cursor, schema_table, data, func_dict)
