{{ config(materialized='table') }}

select
    r.region_key,
    m.month_key,
    s.processing_type,
    s.disposed_count,
    s.timely_count
from {{ ref('stg_snap_timeliness') }} s

join {{ ref('dim_region') }} r
    on s.region = r.region_code

join {{ ref('dim_month') }} m
    on s.reporting_month = m.reporting_month

where s.region in (
    '01', '02/09', '03', '04', '05',
    '06', '07', '08', '10', '11'
)