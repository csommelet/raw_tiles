import raw_tiles.tile_format.msgpack_format as msgpack_format
from raw_tiles.util import st_box2d_for_tile
import psycopg2
import gzip
import boto3


def output_fmt(fmt, conn, z, x, y):
    st_box2d = st_box2d_for_tile(z, x, y)

    query = "select osm_id as fid, st_asbinary(way) as wkb, " \
            "to_json(tags) as json from planet_osm_polygon where " \
            "way && %s" % st_box2d

    with conn.cursor() as cur:
        cur.execute(query)
        for row in cur:
            fid = row[0]
            wkb = row[1]
            props = row[2]

            fmt.write(fid, wkb, props)


def output_io(io, conn, z, x, y):
    with gzip.GzipFile(fileobj=io, mode='wb', compresslevel=9) as fh:
        with msgpack_format.write(fh) as fmt:
            output_fmt(fmt, conn, z, x, y)


def output_tile(s3, output_bucket, conn, z, x, y):
    with tempfile.NamedTemporaryFile() as tmp:
        output_io(tmp, conn, z, x, y)
        key = "%d/%d/%d.msgpack.gz" % (z, x, y)
        s3.meta.client.upload_file(tmp.name, output_bucket, key)


if __name__ == '__main__':
    import sys

    db_params = sys.argv[1]
    z = int(sys.argv[2])
    output_bucket = sys.argv[3]

    conn = psycopg2.connect(db_params)

    s3 = boto3.resource('s3')

    max_coord = 1 << z
    for x in range(0, max_coord):
        for y in range(0, max_coord):
            output_tile(s3, output_bucket, conn, z, x, y)