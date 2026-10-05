{{ config(materialized='table') }}

with all_months as (
    select report_month as reporting_month
    from {{ source('snap_silver', 'snap_eligibility') }}

    union

    select reporting_month
    from {{ ref('stg_snap_timeliness') }}
),

parsed as (
    select
        reporting_month,
        to_date(reporting_month || '-01', 'YYYY-MM-DD') as month_date
    from all_months
)

select
    to_number(to_char(month_date, 'YYYYMM')) as month_key,
    reporting_month,
    year(month_date) as year,
    'Q' || quarter(month_date) as quarter,
    month(month_date) as month_number,
    monthname(month_date) as month_name
from parsed