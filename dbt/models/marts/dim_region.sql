{{ config(materialized='table') }}

select
    region_code::integer as region_key,
    region_code,
    'Region ' || region_code as region_name
from (
    select distinct region_code
    from {{ source('snap_silver', 'county_region_reference') }}
)

union all

select
    12 as region_key,
    '02/09' as region_code,
    'Region 02/09' as region_name