with wide as (
    select *
    from (
        pivot (
            select
                release_date,
                symbol,
                value
            from alternative_data.freight.freight_data
        )
        on symbol
        using first(value)
        group by release_date
    )
)
select
    release_date,
    last_value(columns(* exclude (release_date)) ignore nulls) over (
        order by release_date
        rows between unbounded preceding and current row
    )
from wide
order by release_date