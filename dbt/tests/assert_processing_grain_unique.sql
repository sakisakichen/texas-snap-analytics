select
    region_key,
    month_key,
    processing_type,
    count(*) as row_count
from {{ ref('fact_snap_processing') }}
group by region_key, month_key, processing_type
having count(*) > 1