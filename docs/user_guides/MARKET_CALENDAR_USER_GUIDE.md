# Market Calendar Features User Guide

## Overview

The Historical Data Ingestor now includes powerful market calendar features that provide intelligent trading day awareness, automatic exchange detection, and significant API cost optimization. These features leverage the industry-standard `pandas-market-calendars` library to deliver professional-grade market calendar functionality.

## 🚀 Quick Start

### Basic Usage

```bash
# Analyze trading days for a date range
python main.py market-calendar 2024-01-01 2024-01-31

# Test symbol-to-exchange mapping
python main.py exchange-mapping "ES.FUT,SPY,AAPL"

# Ingest with automatic calendar optimization
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d --symbols ES.FUT --start-date 2024-01-01 --end-date 2024-01-31
```

### Key Benefits

- **30%+ API Cost Reduction**: Automatic filtering of non-trading days
- **Zero Configuration**: Intelligent exchange detection for common symbols
- **Enhanced Accuracy**: Real market calendars with holidays and early closes
- **Rich Feedback**: Clear warnings and optimization suggestions

## 📅 Market Calendar Command

### Basic Analysis

```bash
# Analyze a date range with NYSE calendar (default)
python main.py market-calendar 2024-01-01 2024-01-31
```

**Output:**
```
📅 Market Calendar Analysis: NYSE
Date Range: 2024-01-01 to 2024-01-31
Exchange: NYSE

📊 Summary:
Total days: 31
Trading days: 21
Non-trading days: 10
Trading day coverage: 67.7%
✅ Good trading day coverage for API efficiency
```

### Exchange-Specific Analysis

```bash
# Analyze with specific exchange
python main.py market-calendar 2024-12-23 2024-12-27 --exchange CME_Energy

# Show holidays in the range
python main.py market-calendar 2024-12-01 2024-12-31 --exchange NYSE --holidays

# Show market schedule with open/close times
python main.py market-calendar 2024-01-15 2024-01-19 --schedule
```

### Advanced Options

```bash
# Quick coverage check (minimal output)
python main.py market-calendar 2024-01-01 2024-12-31 --coverage

# List all available exchanges
python main.py market-calendar 2024-01-01 2024-01-02 --list-exchanges
```

## 🎯 Exchange Mapping System

### Automatic Symbol Detection

The system automatically detects the appropriate exchange for common symbols:

| Symbol Type | Example | Detected Exchange | Confidence |
|-------------|---------|-------------------|------------|
| CME Energy Futures | `CL.FUT`, `NG.c.0` | CME_Energy | 95% |
| CME Equity Futures | `ES.FUT`, `NQ.c.0` | CME_Equity | 95% |
| NYSE Equities | `SPY`, `DIA` | NYSE | 90% |
| NASDAQ Stocks | `AAPL`, `MSFT` | NASDAQ | 95% |

### Testing Symbol Mappings

```bash
# Test individual symbol
python main.py exchange-mapping --test "CL.FUT"

# Analyze multiple symbols
python main.py exchange-mapping "ES.FUT,CL.c.0,SPY,AAPL"

# Filter by confidence level
python main.py exchange-mapping "SPY,UNKNOWN_SYMBOL" --min-confidence 0.8
```

### Exchange Information

```bash
# Get detailed exchange information
python main.py exchange-mapping --info CME_Energy

# List all supported exchanges
python main.py exchange-mapping --list

# Show all mapping rules
python main.py exchange-mapping --mappings
```

## 💡 Enhanced Ingest & Query Commands

### Automatic Pre-flight Analysis

Both `ingest` and `query` commands now include intelligent pre-flight checks:

```bash
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d --symbols ES.FUT --start-date 2024-12-23 --end-date 2024-12-27
```

**Enhanced Output:**
```
🎯 Auto-detected exchange: CME_Equity (confidence: 0.95)

📅 Market Calendar Pre-flight Analysis (CME_Equity):
Date Range: 2024-12-23 to 2024-12-27
Trading Days: 3/5 (60.0% coverage)
⚠️ Moderate trading day coverage - consider optimization
💰 Potential API savings: ~40% by excluding non-trading days

🕐 Early Market Closes Detected (1):
   • 2024-12-24 (Tue): 13:00 (Christmas Eve)
💡 Early closes may affect data completeness for intraday schemas
```

### Cost Optimization Warnings

The system provides intelligent warnings about potentially inefficient date ranges:

- **<30% coverage**: Strong warning with confirmation prompt
- **30-60% coverage**: Moderate warning with optimization suggestions  
- **>85% coverage**: Confirmation of excellent efficiency

## 🔧 Configuration Options

### Job-Level Calendar Settings

You can specify exchange calendars in your job configurations:

```yaml
# configs/api_specific/databento_config.yaml
jobs:
  - name: "energy_futures_optimized"
    dataset: "GLBX.MDP3"
    schema: "ohlcv-1d"
    symbols: ["CL.FUT", "NG.FUT"]
    stype_in: "continuous"
    start_date: "2024-01-01"
    end_date: "2024-12-31"
    date_chunk_interval_days: 7
    enable_market_calendar_filtering: true  # Enable calendar filtering
    exchange_name: "CME_Energy"             # Specify exchange
```

### Available Exchanges

| Exchange | Description | Best For |
|----------|-------------|----------|
| `NYSE` | New York Stock Exchange | US equities, ETFs |
| `NASDAQ` | NASDAQ Stock Market | Tech stocks, growth equities |
| `CME_Equity` | CME Equity Index Futures | ES, NQ, RTY futures |
| `CME_Energy` | CME Energy Futures | CL, NG, HO, RB futures |
| `CME_Commodity` | CME Agricultural & Metals | ZC, GC, SI futures |
| `LSE` | London Stock Exchange | UK equities |

## 📊 Performance & Optimization

### API Cost Reduction

Calendar filtering provides significant cost savings:

```bash
# Without filtering: 365 API calls for full year
# With filtering: ~252 API calls (only trading days)
# Savings: 31% reduction in API costs
```

### Performance Characteristics

- **Trading day checks**: 365 days in <5 seconds
- **Schedule retrieval**: Full year in <15 seconds
- **Symbol mapping**: 1000+ symbols in <1 second
- **Memory usage**: Stable with LRU caching

## 🏖️ Holiday & Early Close Detection

### Holiday Analysis

```bash
python main.py market-calendar 2024-01-01 2024-12-31 --exchange NYSE --holidays
```

**Output shows major holidays:**
- New Year's Day
- Martin Luther King Jr. Day  
- Presidents' Day
- Good Friday
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving
- Christmas Day

### Early Close Detection

The system automatically detects early market closes:

- **Black Friday**: 13:00 ET (day after Thanksgiving)
- **Christmas Eve**: 13:00 ET (if weekday)
- **New Year's Eve**: 13:00 ET (if weekday)  
- **Day before July 4th**: 13:00 ET (certain conditions)

## 🛠️ Troubleshooting

### Common Issues

**Exchange not found:**
```bash
python main.py exchange-mapping --list  # See available exchanges
```

**Low confidence mapping:**
```bash
python main.py exchange-mapping --test "YOUR_SYMBOL"  # Test specific symbol
```

**Library not installed:**
```bash
pip install pandas-market-calendars>=5.0
```

### Fallback Behavior

If `pandas-market-calendars` is not available, the system gracefully falls back to:
- Hardcoded US holiday detection
- Basic weekend filtering
- NYSE calendar assumptions

### Performance Tips

1. **Use appropriate date ranges** for each schema type
2. **Enable calendar filtering** for large historical backfills
3. **Check coverage warnings** before long-running operations
4. **Use exchange-specific calendars** for maximum accuracy

## 📚 Advanced Usage

### Custom Workflows

Combine calendar features with existing workflow tools:

```bash
# Check calendar before running backfill
python main.py market-calendar 2024-01-01 2024-12-31 --coverage
python main.py backfill ENERGY_FUTURES --lookback 1y
```

### API Integration

Use calendar features programmatically:

```python
from src.cli.smart_validation import MarketCalendar
from src.cli.exchange_mapping import map_symbols_to_exchange

# Auto-detect exchange
symbols = ["ES.FUT", "CL.FUT"]
exchange, confidence = map_symbols_to_exchange(symbols)

# Create calendar
calendar = MarketCalendar(exchange)
trading_days = calendar.get_trading_days_count(start_date, end_date)
```

### Testing & Validation

Run comprehensive tests:

```bash
python run_calendar_tests.py  # Full test suite with reporting
```

## 🎓 Best Practices

### Date Range Selection

**For Definitions Schema:**
- Use 2-3 weeks for comprehensive coverage
- Wider ranges provide better instrument coverage

**For OHLCV Data:**
- 1 week to 1 month for analysis
- Consider trading day density

**For High-Frequency Data:**
- 1-3 days maximum for trades/TBBO
- Monitor early close warnings

### Production Usage

1. **Enable calendar filtering** for cost optimization
2. **Use specific exchanges** rather than defaults when possible  
3. **Monitor pre-flight warnings** for date range optimization
4. **Test symbol mappings** for new instrument types
5. **Leverage coverage analysis** for planning large backfills

## 🆘 Support

For additional help:

```bash
# CLI help
python main.py market-calendar --help
python main.py exchange-mapping --help

# Interactive help menu
python main.py help-menu

# Troubleshooting guide
python main.py troubleshoot "calendar"
```

---

*This feature significantly enhances the Historical Data Ingestor with professional-grade market calendar functionality, providing immediate cost savings and improved user experience while maintaining complete backward compatibility.*