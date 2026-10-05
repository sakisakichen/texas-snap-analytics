select
    reporting_month,
    "Region" as region,
    processing_type,
    disposed_count,
    timely_count,
    source_percent,
    source_file
from {{ source('snap_silver', 'snap_timeliness') }}