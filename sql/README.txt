SNAP Analytics Platform V2 - Snowflake SQL Prebuild

staging/
  00_setup_snowflake.sql
  01_create_silver_tables.sql
  02_load_silver_from_parquet_template.sql

marts/
  01_create_gold_tables.sql
  02_build_dimensions.sql
  03_build_facts.sql
  04_validate_gold.sql

Recommended execution order after Snowflake trial activation:
1. staging/00_setup_snowflake.sql
2. staging/01_create_silver_tables.sql
3. staging/02_load_silver_from_parquet_template.sql
   - inspect actual Parquet field names first
   - replace file-name placeholders
4. marts/01_create_gold_tables.sql
5. marts/02_build_dimensions.sql
   - replace authoritative Region / County reference placeholders
6. marts/03_build_facts.sql
7. marts/04_validate_gold.sql
8. Publish Trusted Gold only after acceptance criteria pass.

Important:
- The Parquet COPY INTO and authoritative geography reference sections
  intentionally contain placeholders because those details depend on the
  actual Snowflake environment and reference table names.
- Do not blindly execute placeholder blocks.
