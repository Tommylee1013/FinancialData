select
    base_date,
    symbol,
    exchange,
    country,
    close
from market.index_data
where symbol = 'SOX'