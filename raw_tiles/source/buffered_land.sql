SELECT
    gid AS __id__,
    ST_AsBinary(geom) AS __geometry__,
    jsonb_build_object(
      'source', 'tilezen.org',
      'min_zoom', 0,
      'kind', 'maritime',
      'maritime_boundary', TRUE
    ) AS __properties__

FROM (
  SELECT
    gid,
    -- extract only polygons. we might get linestring and point fragments when
    -- the box and geometry touch but don't overlap. we don't want these, so
    -- want to throw them away.
    ST_CollectionExtract(ST_Intersection(the_geom, {{box}}), 3) AS geom

  FROM buffered_land

  WHERE
    the_geom && {{box}}
) maybe_empty_intersections

WHERE
  NOT ST_IsEmpty(geom)
