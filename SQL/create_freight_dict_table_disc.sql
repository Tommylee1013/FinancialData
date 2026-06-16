insert into freight.freight_dictionary (
    table_schema,
    table_name,
    column_name,
    ordinal_position,
    data_type,
    is_nullable,
    is_primary_key,
    description,
    example_value,
    note
)
values
(
    'freight',
    'freight_data',
    'base_date',
    1,
    'date',
    0,
    1,
    'reference date of the freight index observation.',
    '2026-06-16',
    'usually represents the market date or index base date.'
),
(
    'freight',
    'freight_data',
    'release_date',
    2,
    'date',
    0,
    0,
    'date on which the freight index value was released or became available.',
    '2026-06-16',
    'used to prevent look-ahead bias in historical analysis.'
),
(
    'freight',
    'freight_data',
    'time',
    3,
    'time',
    0,
    0,
    'local release time of the freight index.',
    '13:00:00',
    'release time differs by freight index series.'
),
(
    'freight',
    'freight_data',
    'time_zone',
    4,
    'varchar',
    0,
    0,
    'utc offset of the local release time.',
    'utc+1',
    'for london-based indices, this may change between utc+0 and utc+1 depending on daylight saving time.'
),
(
    'freight',
    'freight_data',
    'symbol',
    5,
    'varchar',
    0,
    1,
    'standardized internal symbol of the freight index.',
    'bdi',
    'examples include bdi, bsi, bcti, bpi, bhsi, blng, blpg, fbx, and bdti.'
),
(
    'freight',
    'freight_data',
    'exchange',
    6,
    'varchar',
    0,
    1,
    'data source, benchmark provider, or exchange code.',
    'baltic',
    'represents the source institution or index provider.'
),
(
    'freight',
    'freight_data',
    'country',
    7,
    'varchar',
    0,
    0,
    'country associated with the index provider or benchmark source.',
    'united kingdom',
    'this is provider country, not necessarily the economic exposure region.'
),
(
    'freight',
    'freight_data',
    'value',
    8,
    'double',
    0,
    0,
    'observed numeric value of the freight index.',
    '2145.0',
    'stored as a numeric time-series value.'
);