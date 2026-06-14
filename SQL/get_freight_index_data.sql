select
    base_date,
    symbol,
    value
    from alternative_data.freight.freight_data
where symbol = 'WCI'

select * from alternative_data.freight.freight_data