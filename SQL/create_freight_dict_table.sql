-- Create Freight dictionary table query

create table if not exists freight.freight_dictionary (
    table_schema varchar,
    table_name varchar,
    column_name varchar,
    ordinal_position integer,
    data_type varchar,
    is_nullable tinyint check (is_nullable in (0, 1)),
    is_primary_key tinyint check (is_primary_key in (0, 1)),
    description varchar,
    example_value varchar,
    note varchar
);

delete from alternative_data.freight_dictionary
where table_schema = 'freight'
  and table_name = 'freight_data';