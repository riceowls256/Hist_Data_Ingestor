-- SQL Verification Queries for Story 2.7 Database Validation
-- These queries can be run directly in psql or pgAdmin to verify data integrity

-- ==========================================
-- GENERAL DATA OVERVIEW
-- ==========================================

-- 1. Overall record counts across all tables
SELECT 
    'daily_ohlcv_data' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN data_source = 'databento' THEN 1 END) as databento_records,
    MIN(ts_event) as earliest_timestamp,
    MAX(ts_event) as latest_timestamp
FROM daily_ohlcv_data
UNION ALL
SELECT 
    'trades_data',
    COUNT(*),
    COUNT(CASE WHEN data_source = 'databento' THEN 1 END),
    MIN(ts_event),
    MAX(ts_event)
FROM trades_data
UNION ALL
SELECT 
    'tbbo_data',
    COUNT(*),
    COUNT(CASE WHEN data_source = 'databento' THEN 1 END),
    MIN(ts_event),
    MAX(ts_event)
FROM tbbo_data
UNION ALL
SELECT 
    'statistics_data',
    COUNT(*),
    COUNT(CASE WHEN data_source = 'databento' THEN 1 END),
    MIN(ts_event),
    MAX(ts_event)
FROM statistics_data
UNION ALL
SELECT 
    'definitions_data',
    COUNT(*),
    COUNT(CASE WHEN data_source = 'databento' THEN 1 END),
    MIN(ts_event),
    MAX(ts_event)
FROM definitions_data;

-- ==========================================
-- OHLCV DATA VERIFICATION
-- ==========================================

-- 2. OHLCV data integrity checks
SELECT 
    COUNT(*) as total_ohlcv_records,
    COUNT(DISTINCT instrument_id) as unique_instruments,
    COUNT(DISTINCT symbol) as unique_symbols,
    MIN(ts_event) as earliest_timestamp,
    MAX(ts_event) as latest_timestamp,
    AVG(volume) as avg_volume,
    MIN(open_price) as min_open,
    MAX(high_price) as max_high
FROM daily_ohlcv_data 
WHERE data_source = 'databento';

-- 3. OHLCV business logic validation (should return 0 for all)
SELECT 
    COUNT(*) as invalid_high_low_records
FROM daily_ohlcv_data 
WHERE data_source = 'databento' 
AND high_price < low_price;

SELECT 
    COUNT(*) as invalid_high_open_records
FROM daily_ohlcv_data 
WHERE data_source = 'databento' 
AND high_price < open_price;

SELECT 
    COUNT(*) as invalid_high_close_records
FROM daily_ohlcv_data 
WHERE data_source = 'databento' 
AND high_price < close_price;

SELECT 
    COUNT(*) as negative_price_records
FROM daily_ohlcv_data 
WHERE data_source = 'databento' 
AND (open_price <= 0 OR high_price <= 0 OR low_price <= 0 OR close_price <= 0);

-- 4. OHLCV sample data inspection
SELECT 
    symbol,
    ts_event,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    granularity
FROM daily_ohlcv_data 
WHERE data_source = 'databento'
ORDER BY ts_event DESC 
LIMIT 5;

-- ==========================================
-- TRADES DATA VERIFICATION
-- ==========================================

-- 5. Trades data integrity
SELECT 
    COUNT(*) as total_trade_records,
    COUNT(DISTINCT instrument_id) as unique_instruments,
    SUM(size) as total_volume,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    MIN(ts_event) as earliest_trade,
    MAX(ts_event) as latest_trade
FROM trades_data 
WHERE data_source = 'databento';

-- 6. Invalid trades validation (should return 0)
SELECT 
    COUNT(*) as invalid_price_trades
FROM trades_data 
WHERE data_source = 'databento' 
AND price <= 0;

SELECT 
    COUNT(*) as invalid_size_trades
FROM trades_data 
WHERE data_source = 'databento' 
AND size <= 0;

-- 7. Trades sample data
SELECT 
    symbol,
    ts_event,
    price,
    size,
    instrument_id
FROM trades_data 
WHERE data_source = 'databento'
ORDER BY ts_event DESC 
LIMIT 5;

-- ==========================================
-- TBBO DATA VERIFICATION
-- ==========================================

-- 8. TBBO data integrity
SELECT 
    COUNT(*) as total_tbbo_records,
    COUNT(DISTINCT instrument_id) as unique_instruments,
    COUNT(CASE WHEN bid_price IS NOT NULL THEN 1 END) as records_with_bid,
    COUNT(CASE WHEN ask_price IS NOT NULL THEN 1 END) as records_with_ask,
    AVG(bid_price) as avg_bid,
    AVG(ask_price) as avg_ask
FROM tbbo_data 
WHERE data_source = 'databento';

-- 9. TBBO spread validation (should return 0)
SELECT 
    COUNT(*) as invalid_spread_records
FROM tbbo_data 
WHERE data_source = 'databento'
AND bid_price IS NOT NULL 
AND ask_price IS NOT NULL
AND ask_price < bid_price;

-- 10. TBBO sample data
SELECT 
    symbol,
    ts_event,
    bid_price,
    ask_price,
    bid_size,
    ask_size
FROM tbbo_data 
WHERE data_source = 'databento'
ORDER BY ts_event DESC 
LIMIT 5;

-- ==========================================
-- STATISTICS DATA VERIFICATION
-- ==========================================

-- 11. Statistics data overview
SELECT 
    COUNT(*) as total_statistics_records,
    COUNT(DISTINCT instrument_id) as unique_instruments,
    COUNT(DISTINCT stat_type) as unique_stat_types,
    MIN(ts_event) as earliest_stat,
    MAX(ts_event) as latest_stat
FROM statistics_data 
WHERE data_source = 'databento';

-- 12. Statistics types breakdown
SELECT 
    stat_type,
    COUNT(*) as count,
    AVG(stat_value) as avg_value
FROM statistics_data 
WHERE data_source = 'databento'
GROUP BY stat_type
ORDER BY count DESC;

-- ==========================================
-- DEFINITIONS DATA VERIFICATION
-- ==========================================

-- 13. Definitions data overview
SELECT 
    COUNT(*) as total_definition_records,
    COUNT(DISTINCT instrument_id) as unique_instruments,
    MIN(ts_event) as earliest_definition,
    MAX(ts_event) as latest_definition
FROM definitions_data 
WHERE data_source = 'databento';

-- 14. Definitions sample data
SELECT 
    symbol,
    instrument_id,
    ts_event,
    symbol_type
FROM definitions_data 
WHERE data_source = 'databento'
ORDER BY ts_event DESC 
LIMIT 5;

-- ==========================================
-- IDEMPOTENCY VERIFICATION
-- ==========================================

-- 15. Check for duplicate OHLCV records (should return 0)
SELECT 
    instrument_id, 
    ts_event, 
    granularity,
    COUNT(*) as duplicate_count
FROM daily_ohlcv_data 
WHERE data_source = 'databento'
GROUP BY instrument_id, ts_event, granularity
HAVING COUNT(*) > 1;

-- 16. Check for duplicate trades (should return 0)
SELECT 
    instrument_id, 
    ts_event, 
    price, 
    size,
    COUNT(*) as duplicate_count
FROM trades_data 
WHERE data_source = 'databento'
GROUP BY instrument_id, ts_event, price, size
HAVING COUNT(*) > 1;

-- 17. Check for duplicate TBBO records (should return 0)
SELECT 
    instrument_id, 
    ts_event,
    COUNT(*) as duplicate_count
FROM tbbo_data 
WHERE data_source = 'databento'
GROUP BY instrument_id, ts_event
HAVING COUNT(*) > 1;

-- 18. Check for duplicate statistics (should return 0)
SELECT 
    instrument_id, 
    ts_event, 
    stat_type,
    COUNT(*) as duplicate_count
FROM statistics_data 
WHERE data_source = 'databento'
GROUP BY instrument_id, ts_event, stat_type
HAVING COUNT(*) > 1;

-- 19. Check for duplicate definitions (should return 0)
SELECT 
    instrument_id, 
    ts_event,
    COUNT(*) as duplicate_count
FROM definitions_data 
WHERE data_source = 'databento'
GROUP BY instrument_id, ts_event
HAVING COUNT(*) > 1;

-- ==========================================
-- DATA QUALITY SUMMARY REPORT
-- ==========================================

-- 20. Comprehensive data quality summary
WITH data_quality AS (
    SELECT 
        'OHLCV' as data_type,
        COUNT(*) as record_count,
        COUNT(DISTINCT instrument_id) as unique_instruments,
        0 as invalid_records
    FROM daily_ohlcv_data 
    WHERE data_source = 'databento'
    
    UNION ALL
    
    SELECT 
        'TRADES' as data_type,
        COUNT(*) as record_count,
        COUNT(DISTINCT instrument_id) as unique_instruments,
        COUNT(CASE WHEN price <= 0 OR size <= 0 THEN 1 END) as invalid_records
    FROM trades_data 
    WHERE data_source = 'databento'
    
    UNION ALL
    
    SELECT 
        'TBBO' as data_type,
        COUNT(*) as record_count,
        COUNT(DISTINCT instrument_id) as unique_instruments,
        COUNT(CASE WHEN bid_price IS NOT NULL AND ask_price IS NOT NULL AND ask_price < bid_price THEN 1 END) as invalid_records
    FROM tbbo_data 
    WHERE data_source = 'databento'
    
    UNION ALL
    
    SELECT 
        'STATISTICS' as data_type,
        COUNT(*) as record_count,
        COUNT(DISTINCT instrument_id) as unique_instruments,
        0 as invalid_records
    FROM statistics_data 
    WHERE data_source = 'databento'
    
    UNION ALL
    
    SELECT 
        'DEFINITIONS' as data_type,
        COUNT(*) as record_count,
        COUNT(DISTINCT instrument_id) as unique_instruments,
        0 as invalid_records
    FROM definitions_data 
    WHERE data_source = 'databento'
)
SELECT 
    data_type,
    record_count,
    unique_instruments,
    invalid_records,
    CASE 
        WHEN record_count = 0 THEN 'NO_DATA'
        WHEN invalid_records = 0 THEN 'CLEAN'
        ELSE 'ISSUES_FOUND'
    END as data_quality_status
FROM data_quality
ORDER BY record_count DESC; 