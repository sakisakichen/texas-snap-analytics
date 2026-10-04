select *
from {{ ref('fact_snap_processing') }}
where disposed_count < 0
   or timely_count < 0
   or timely_count > disposed_count