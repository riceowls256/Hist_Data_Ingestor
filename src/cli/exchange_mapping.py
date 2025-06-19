"""
Intelligent symbol-to-exchange mapping for market calendar optimization.

This module provides automatic detection of the appropriate market calendar exchange
based on symbol patterns, instrument types, and market conventions. It eliminates
the need for users to manually specify exchanges in most cases.
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class AssetClass(Enum):
    """Asset class categories for exchange mapping."""
    EQUITY = "equity"
    FUTURES = "futures" 
    OPTIONS = "options"
    FX = "fx"
    CRYPTO = "crypto"
    BOND = "bond"
    COMMODITY = "commodity"


class MarketRegion(Enum):
    """Market regions for geographic exchange mapping."""
    US = "us"
    EUROPE = "europe"
    ASIA = "asia"
    GLOBAL = "global"


@dataclass
class SymbolMapping:
    """Mapping configuration for a symbol pattern."""
    pattern: str  # Regex pattern to match symbols
    exchange: str  # Target exchange calendar name
    asset_class: AssetClass
    region: MarketRegion
    description: str
    confidence: float = 1.0  # Confidence level (0.0-1.0)
    examples: List[str] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []


class ExchangeMapper:
    """
    Intelligent symbol-to-exchange mapping system.
    
    Automatically detects the appropriate market calendar exchange based on
    symbol patterns, providing accurate calendar selection without user input.
    """

    def __init__(self):
        """Initialize the exchange mapper with predefined mapping rules."""
        self.mappings: List[SymbolMapping] = []
        self._load_default_mappings()
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()

    def _load_default_mappings(self):
        """Load comprehensive default symbol-to-exchange mappings."""
        
        # CME Energy Futures - High Priority
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^(CL|NG|HO|RB|BZ)\.(?:FUT|c\.\d+|[A-Z]\d{2})$",
                exchange="CME_Energy",
                asset_class=AssetClass.FUTURES,
                region=MarketRegion.US,
                description="CME Energy futures (Oil, Gas, Refined products)",
                confidence=0.95,
                examples=["CL.FUT", "NG.c.0", "HO.H24", "RB.FUT", "BZ.c.0"]
            ),
            SymbolMapping(
                pattern=r"^(WTI|BRENT|GASOLINE|HEATING_OIL)\b",
                exchange="CME_Energy", 
                asset_class=AssetClass.COMMODITY,
                region=MarketRegion.US,
                description="Energy commodity aliases",
                confidence=0.90,
                examples=["WTI", "BRENT", "GASOLINE"]
            )
        ])

        # CME Equity Index Futures
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^(ES|NQ|RTY|YM)\.(?:FUT|c\.\d+|[A-Z]\d{2})$",
                exchange="CME_Equity",
                asset_class=AssetClass.FUTURES,
                region=MarketRegion.US,
                description="CME Equity index futures (S&P, NASDAQ, Russell, Dow)",
                confidence=0.95,
                examples=["ES.FUT", "NQ.c.0", "RTY.H24", "YM.FUT"]
            ),
            SymbolMapping(
                pattern=r"^(SPX|NDX|RUT|DJI)\.(?:FUT|c\.\d+)$",
                exchange="CME_Equity",
                asset_class=AssetClass.FUTURES, 
                region=MarketRegion.US,
                description="Index future aliases",
                confidence=0.90,
                examples=["SPX.FUT", "NDX.c.0"]
            )
        ])

        # CME Agricultural and Metals
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^(ZC|ZS|ZW|ZL|ZM|GC|SI|HG|PA|PL)\.(?:FUT|c\.\d+|[A-Z]\d{2})$",
                exchange="CME_Commodity",
                asset_class=AssetClass.FUTURES,
                region=MarketRegion.US,
                description="CME Agricultural and metals futures",
                confidence=0.95,
                examples=["ZC.FUT", "GC.c.0", "SI.H24", "HG.FUT"]
            )
        ])

        # US Equities - NYSE
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^(SPY|IWM|DIA|XLF|XLE|XLU|XLK|XLV|XLI|XLP|XLY|XLB|XLRE|XRT)$",
                exchange="NYSE",
                asset_class=AssetClass.EQUITY,
                region=MarketRegion.US,
                description="Major NYSE-listed ETFs and sector funds",
                confidence=0.90,
                examples=["SPY", "IWM", "DIA", "XLF", "XLE"]
            ),
            SymbolMapping(
                pattern=r"^[A-Z]{1,4}$",  # Generic US equity pattern
                exchange="NYSE",
                asset_class=AssetClass.EQUITY,
                region=MarketRegion.US,
                description="Generic US equity symbols (NYSE default)",
                confidence=0.60,
                examples=["IBM", "GE", "F", "T"]
            )
        ])

        # US Equities - NASDAQ
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^(QQQ|TQQQ|SQQQ|TLT|IEF|AGG)$",
                exchange="NASDAQ",
                asset_class=AssetClass.EQUITY,
                region=MarketRegion.US,
                description="Major NASDAQ-listed ETFs",
                confidence=0.90,
                examples=["QQQ", "TQQQ", "TLT", "AGG"]
            ),
            SymbolMapping(
                pattern=r"^(AAPL|MSFT|GOOGL|GOOG|AMZN|TSLA|NVDA|META|NFLX|ADBE)$",
                exchange="NASDAQ",
                asset_class=AssetClass.EQUITY,
                region=MarketRegion.US,
                description="Major NASDAQ tech stocks",
                confidence=0.95,
                examples=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
            )
        ])

        # Currency Futures
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^(6E|6J|6B|6A|6C|6S|6N)\.(?:FUT|c\.\d+|[A-Z]\d{2})$",
                exchange="CME_FX",
                asset_class=AssetClass.FX,
                region=MarketRegion.GLOBAL,
                description="CME Currency futures",
                confidence=0.95,
                examples=["6E.FUT", "6J.c.0", "6B.H24"]
            )
        ])

        # Interest Rate Futures  
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^(ZB|ZN|ZF|ZT|GE)\.(?:FUT|c\.\d+|[A-Z]\d{2})$",
                exchange="CME_InterestRate",
                asset_class=AssetClass.BOND,
                region=MarketRegion.US,
                description="CME Interest rate and bond futures",
                confidence=0.95,
                examples=["ZB.FUT", "ZN.c.0", "GE.H24"]
            )
        ])

        # European Markets
        self.mappings.extend([
            SymbolMapping(
                pattern=r"^[A-Z]{2,4}\.L$",
                exchange="LSE",
                asset_class=AssetClass.EQUITY,
                region=MarketRegion.EUROPE,
                description="London Stock Exchange equities",
                confidence=0.85,
                examples=["VODL.L", "BP.L", "SHEL.L"]
            ),
            SymbolMapping(
                pattern=r"^[A-Z]{3}\.DE$",
                exchange="XETR",
                asset_class=AssetClass.EQUITY,
                region=MarketRegion.EUROPE,
                description="Deutsche Börse XETRA equities",
                confidence=0.85,
                examples=["SAP.DE", "BMW.DE", "SIE.DE"]
            )
        ])

        # Sort by confidence (highest first)
        self.mappings.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Loaded {len(self.mappings)} symbol-to-exchange mapping rules")

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for mapping in self.mappings:
            try:
                self._compiled_patterns[mapping.pattern] = re.compile(mapping.pattern, re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Failed to compile pattern '{mapping.pattern}': {e}")

    def map_symbol_to_exchange(
        self, 
        symbol: str, 
        fallback_exchange: str = "NYSE"
    ) -> Tuple[str, float, Optional[SymbolMapping]]:
        """
        Map a symbol to its most appropriate exchange calendar.

        Args:
            symbol: Financial symbol to map
            fallback_exchange: Default exchange if no matches found

        Returns:
            Tuple of (exchange_name, confidence, mapping_info)
        """
        symbol = symbol.strip().upper()
        
        # Try each mapping in order of confidence
        for mapping in self.mappings:
            pattern = self._compiled_patterns.get(mapping.pattern)
            if pattern and pattern.match(symbol):
                logger.debug(f"Mapped symbol '{symbol}' to exchange '{mapping.exchange}'",
                           symbol=symbol,
                           exchange=mapping.exchange,
                           confidence=mapping.confidence,
                           asset_class=mapping.asset_class.value)
                return mapping.exchange, mapping.confidence, mapping

        # No matches found
        logger.info(f"No exchange mapping found for symbol '{symbol}', using fallback '{fallback_exchange}'",
                   symbol=symbol,
                   fallback=fallback_exchange)
        return fallback_exchange, 0.5, None

    def map_symbols_to_exchange(
        self, 
        symbols: List[str], 
        fallback_exchange: str = "NYSE"
    ) -> Tuple[str, float, Dict[str, SymbolMapping]]:
        """
        Map multiple symbols to the most appropriate single exchange.

        Uses the highest confidence exchange that covers the most symbols.
        Prefers exchanges that can handle multiple symbols over individual mappings.

        Args:
            symbols: List of financial symbols to map
            fallback_exchange: Default exchange if no matches found

        Returns:
            Tuple of (exchange_name, average_confidence, symbol_mappings)
        """
        if not symbols:
            return fallback_exchange, 0.5, {}

        symbol_mappings = {}
        exchange_votes = {}  # exchange -> (total_confidence, symbol_count)
        
        # Map each symbol individually
        for symbol in symbols:
            exchange, confidence, mapping = self.map_symbol_to_exchange(symbol, fallback_exchange)
            symbol_mappings[symbol] = mapping
            
            if exchange not in exchange_votes:
                exchange_votes[exchange] = (0.0, 0)
            
            current_conf, current_count = exchange_votes[exchange]
            exchange_votes[exchange] = (current_conf + confidence, current_count + 1)

        # Find the best exchange based on weighted confidence
        if exchange_votes:
            best_exchange = max(exchange_votes.keys(), 
                              key=lambda ex: exchange_votes[ex][0] / exchange_votes[ex][1])
            total_conf, symbol_count = exchange_votes[best_exchange]
            avg_confidence = total_conf / symbol_count
            
            logger.info(f"Mapped {len(symbols)} symbols to exchange '{best_exchange}'",
                       symbols=symbols,
                       exchange=best_exchange,
                       confidence=avg_confidence,
                       symbol_count=symbol_count)
            
            return best_exchange, avg_confidence, symbol_mappings
        
        return fallback_exchange, 0.5, symbol_mappings

    def get_exchange_info(self, exchange: str) -> Dict[str, any]:
        """Get information about a specific exchange."""
        exchange_info = {
            "NYSE": {
                "name": "New York Stock Exchange",
                "region": "US",
                "asset_classes": ["equity", "etf"],
                "trading_hours": "09:30-16:00 ET",
                "holidays": "US Federal holidays"
            },
            "NASDAQ": {
                "name": "NASDAQ Stock Market", 
                "region": "US",
                "asset_classes": ["equity", "etf"],
                "trading_hours": "09:30-16:00 ET", 
                "holidays": "US Federal holidays"
            },
            "CME_Equity": {
                "name": "CME Equity Index Futures",
                "region": "US",
                "asset_classes": ["futures", "options"],
                "trading_hours": "17:00-16:00 CT (nearly 24h)",
                "holidays": "CME holidays"
            },
            "CME_Energy": {
                "name": "CME Energy Futures",
                "region": "US", 
                "asset_classes": ["futures", "options"],
                "trading_hours": "17:00-16:00 CT (nearly 24h)",
                "holidays": "CME holidays"
            },
            "CME_Commodity": {
                "name": "CME Agricultural & Metals",
                "region": "US",
                "asset_classes": ["futures", "options"],
                "trading_hours": "Various by product",
                "holidays": "CME holidays"
            },
            "LSE": {
                "name": "London Stock Exchange",
                "region": "Europe",
                "asset_classes": ["equity", "etf"],
                "trading_hours": "08:00-16:30 GMT",
                "holidays": "UK bank holidays"
            }
        }
        
        return exchange_info.get(exchange, {
            "name": exchange,
            "region": "Unknown",
            "asset_classes": ["unknown"],
            "trading_hours": "Unknown",
            "holidays": "Unknown"
        })

    def suggest_symbols_for_exchange(self, exchange: str, limit: int = 10) -> List[str]:
        """Suggest example symbols that would map to a given exchange."""
        suggestions = []
        
        for mapping in self.mappings:
            if mapping.exchange == exchange:
                suggestions.extend(mapping.examples[:limit//len([m for m in self.mappings if m.exchange == exchange])])
                if len(suggestions) >= limit:
                    break
                    
        return suggestions[:limit]

    def validate_symbol_exchange_pair(self, symbol: str, exchange: str) -> Tuple[bool, str]:
        """
        Validate if a symbol is appropriate for a given exchange.
        
        Returns:
            Tuple of (is_valid, reason)
        """
        detected_exchange, confidence, mapping = self.map_symbol_to_exchange(symbol)
        
        if detected_exchange == exchange:
            return True, f"Symbol '{symbol}' is appropriate for {exchange} (confidence: {confidence:.2f})"
        elif confidence < 0.7:
            return True, f"Symbol '{symbol}' could work with {exchange} (low confidence detection)"
        else:
            return False, f"Symbol '{symbol}' is better suited for {detected_exchange} (confidence: {confidence:.2f})"


# Global instance
_exchange_mapper = None

def get_exchange_mapper() -> ExchangeMapper:
    """Get the global ExchangeMapper instance."""
    global _exchange_mapper
    if _exchange_mapper is None:
        _exchange_mapper = ExchangeMapper()
    return _exchange_mapper

def map_symbols_to_exchange(symbols: List[str], fallback: str = "NYSE") -> Tuple[str, float]:
    """Convenience function to map symbols to exchange."""
    mapper = get_exchange_mapper()
    exchange, confidence, _ = mapper.map_symbols_to_exchange(symbols, fallback)
    return exchange, confidence

def map_symbol_to_exchange(symbol: str, fallback: str = "NYSE") -> Tuple[str, float]:
    """Convenience function to map a single symbol to exchange."""
    mapper = get_exchange_mapper()
    exchange, confidence, _ = mapper.map_symbol_to_exchange(symbol, fallback)
    return exchange, confidence