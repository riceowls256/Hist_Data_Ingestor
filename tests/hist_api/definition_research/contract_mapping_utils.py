#!/usr/bin/env python3
"""
Contract Mapping Utilities
Helper functions for cross-referencing contracts in other analysis
Use these functions to integrate definition schema mappings with your analysis
"""

import pandas as pd
from datetime import datetime

# Standard futures month codes
MONTH_CODES = {
    'F': 1,  'G': 2,  'H': 3,  'J': 4,  'K': 5,  'M': 6,
    'N': 7,  'Q': 8,  'U': 9,  'V': 10, 'X': 11, 'Z': 12
}

MONTH_NAMES = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}

def get_contract_month_year(symbol):
    """
    Quick function to get month and year from contract symbol
    
    Args:
        symbol (str): Contract symbol like 'ESM5', 'CLZ4', etc.
    
    Returns:
        tuple: (month_number, full_year) or (None, None) if parsing fails
    
    Examples:
        >>> get_contract_month_year('ESM5')
        (6, 2025)
        >>> get_contract_month_year('CLZ4')
        (12, 2024)
    """
    if len(symbol) < 3:
        return None, None
    
    # Look for month code (letter) and year (number)
    for i, char in enumerate(symbol):
        if char in MONTH_CODES and i < len(symbol) - 1:
            month_code = char
            year_digits = symbol[i+1:]
            if year_digits.isdigit():
                year_num = int(year_digits)
                # Convert 2-digit year to 4-digit
                full_year = 2000 + year_num if year_num < 50 else 1900 + year_num
                return MONTH_CODES[month_code], full_year
    
    return None, None

def get_month_name(symbol):
    """
    Get month name from contract symbol
    
    Args:
        symbol (str): Contract symbol
    
    Returns:
        str: Month name or 'Unknown'
    """
    month, year = get_contract_month_year(symbol)
    return MONTH_NAMES.get(month, 'Unknown')

def is_front_month(symbol, contract_mappings):
    """
    Check if symbol is the front month contract
    
    Args:
        symbol (str): Contract symbol to check
        contract_mappings (dict): Continuous contract mappings from DefinitionSchemaMapper
    
    Returns:
        bool: True if this is the front month contract
    """
    if 'Front Month' in contract_mappings:
        return contract_mappings['Front Month']['symbol'] == symbol
    return False

def get_contract_type(symbol):
    """
    Classify contract type (quarterly, monthly, etc.)
    
    Args:
        symbol (str): Contract symbol
    
    Returns:
        str: 'Quarterly', 'Monthly', or 'Unknown'
    """
    month, year = get_contract_month_year(symbol)
    if month in [3, 6, 9, 12]:  # H, M, U, Z
        return 'Quarterly'
    elif month:
        return 'Monthly'
    return 'Unknown'

def is_quarterly_contract(symbol):
    """
    Check if contract is a quarterly contract (H, M, U, Z)
    
    Args:
        symbol (str): Contract symbol
    
    Returns:
        bool: True if quarterly contract
    """
    return get_contract_type(symbol) == 'Quarterly'

def get_contract_quarter(symbol):
    """
    Get quarter for quarterly contracts
    
    Args:
        symbol (str): Contract symbol
    
    Returns:
        str: 'Q1', 'Q2', 'Q3', 'Q4', or None
    """
    month, year = get_contract_month_year(symbol)
    if month == 3:
        return 'Q1'
    elif month == 6:
        return 'Q2'
    elif month == 9:
        return 'Q3'
    elif month == 12:
        return 'Q4'
    return None

def days_to_expiration(symbol, contract_mappings):
    """
    Calculate days to expiration for a contract
    
    Args:
        symbol (str): Contract symbol
        contract_mappings (dict): Contract mappings with expiration dates
    
    Returns:
        int: Days to expiration or None
    """
    for label, contract in contract_mappings.items():
        if contract['symbol'] == symbol:
            if 'expiration' in contract and contract['expiration']:
                exp_date = pd.to_datetime(contract['expiration'])
                return (exp_date - pd.Timestamp.now()).days
    return None

def find_next_contract(symbol, contract_mappings):
    """
    Find the next contract in the chain
    
    Args:
        symbol (str): Current contract symbol
        contract_mappings (dict): Continuous contract mappings
    
    Returns:
        dict: Next contract info or None
    """
    # Find current contract position
    for i, (label, contract) in enumerate(contract_mappings.items()):
        if contract['symbol'] == symbol:
            # Get next contract
            labels = list(contract_mappings.keys())
            if i + 1 < len(labels):
                next_label = labels[i + 1]
                return contract_mappings[next_label]
    return None

def get_roll_date_estimate(symbol, contract_mappings, days_before_expiry=5):
    """
    Estimate roll date (typically a few days before expiration)
    
    Args:
        symbol (str): Contract symbol
        contract_mappings (dict): Contract mappings
        days_before_expiry (int): Days before expiration to roll
    
    Returns:
        datetime: Estimated roll date or None
    """
    for label, contract in contract_mappings.items():
        if contract['symbol'] == symbol:
            if 'expiration' in contract and contract['expiration']:
                exp_date = pd.to_datetime(contract['expiration'])
                return exp_date - pd.Timedelta(days=days_before_expiry)
    return None

def create_contract_lookup_table(contract_mappings):
    """
    Create a lookup table for fast contract information retrieval
    
    Args:
        contract_mappings (dict): Continuous contract mappings
    
    Returns:
        dict: Symbol -> contract info mapping
    """
    lookup = {}
    for label, contract in contract_mappings.items():
        symbol = contract['symbol']
        lookup[symbol] = {
            'label': label,
            'month': contract.get('month'),
            'year': contract.get('year'),
            'month_name': contract.get('month_name'),
            'expiration': contract.get('expiration'),
            'instrument_id': contract.get('instrument_id'),
            'tick_size': contract.get('tick_size'),
            'is_front_month': label == 'Front Month',
            'is_quarterly': get_contract_type(symbol) == 'Quarterly',
            'quarter': get_contract_quarter(symbol)
        }
    return lookup

def filter_contracts_by_criteria(contract_mappings, **criteria):
    """
    Filter contracts by various criteria
    
    Args:
        contract_mappings (dict): Contract mappings
        **criteria: Filtering criteria (quarterly=True, front_month=True, etc.)
    
    Returns:
        dict: Filtered contract mappings
    """
    filtered = {}
    
    for label, contract in contract_mappings.items():
        symbol = contract['symbol']
        include = True
        
        # Check quarterly filter
        if 'quarterly' in criteria:
            is_quarterly = get_contract_type(symbol) == 'Quarterly'
            if criteria['quarterly'] != is_quarterly:
                include = False
        
        # Check front month filter
        if 'front_month' in criteria:
            is_front = label == 'Front Month'
            if criteria['front_month'] != is_front:
                include = False
        
        # Check month filter
        if 'month' in criteria:
            month, _ = get_contract_month_year(symbol)
            if month != criteria['month']:
                include = False
        
        # Check year filter
        if 'year' in criteria:
            _, year = get_contract_month_year(symbol)
            if year != criteria['year']:
                include = False
        
        if include:
            filtered[label] = contract
    
    return filtered

# Example usage functions for integration with other analysis

def integrate_with_price_analysis(price_data, contract_mappings):
    """
    Example: Integrate contract mappings with price analysis
    
    Args:
        price_data (DataFrame): Price data with symbol column
        contract_mappings (dict): Contract mappings
    
    Returns:
        DataFrame: Enhanced price data with contract info
    """
    # Create lookup table
    lookup = create_contract_lookup_table(contract_mappings)
    
    # Add contract information to price data
    enhanced_data = price_data.copy()
    
    enhanced_data['month'] = enhanced_data['symbol'].apply(
        lambda x: lookup.get(x, {}).get('month')
    )
    enhanced_data['year'] = enhanced_data['symbol'].apply(
        lambda x: lookup.get(x, {}).get('year')
    )
    enhanced_data['month_name'] = enhanced_data['symbol'].apply(
        lambda x: lookup.get(x, {}).get('month_name')
    )
    enhanced_data['is_front_month'] = enhanced_data['symbol'].apply(
        lambda x: lookup.get(x, {}).get('is_front_month', False)
    )
    enhanced_data['is_quarterly'] = enhanced_data['symbol'].apply(
        lambda x: lookup.get(x, {}).get('is_quarterly', False)
    )
    enhanced_data['contract_type'] = enhanced_data['symbol'].apply(get_contract_type)
    
    return enhanced_data

def create_roll_schedule(contract_mappings, days_before_expiry=5):
    """
    Create a roll schedule for contract management
    
    Args:
        contract_mappings (dict): Contract mappings
        days_before_expiry (int): Days before expiration to roll
    
    Returns:
        DataFrame: Roll schedule with dates and contract transitions
    """
    roll_schedule = []
    
    for label, contract in contract_mappings.items():
        if 'expiration' in contract and contract['expiration']:
            exp_date = pd.to_datetime(contract['expiration'])
            roll_date = exp_date - pd.Timedelta(days=days_before_expiry)
            
            # Find next contract
            next_contract = find_next_contract(contract['symbol'], contract_mappings)
            
            roll_schedule.append({
                'current_symbol': contract['symbol'],
                'current_month': contract.get('month_name'),
                'expiration_date': exp_date,
                'roll_date': roll_date,
                'next_symbol': next_contract['symbol'] if next_contract else None,
                'next_month': next_contract.get('month_name') if next_contract else None,
                'days_to_roll': (roll_date - pd.Timestamp.now()).days
            })
    
    return pd.DataFrame(roll_schedule).sort_values('roll_date')

# Usage example:
"""
# In your analysis script:

from definition_schema_utility import DefinitionSchemaMapper
from contract_mapping_utils import *

# Load contract mappings
mapper = DefinitionSchemaMapper()
mapper.load_definitions(asset_filter="ES")
continuous = mapper.get_continuous_contract_mapping("ES")

# Use utility functions in your analysis
for symbol in your_symbol_list:
    month, year = get_contract_month_year(symbol)
    is_front = is_front_month(symbol, continuous)
    contract_type = get_contract_type(symbol)
    days_left = days_to_expiration(symbol, continuous)
    
    print(f"{symbol}: {get_month_name(symbol)} {year}, "
          f"Type: {contract_type}, "
          f"Front: {is_front}, "
          f"Days to expiry: {days_left}")

# Create enhanced datasets
enhanced_prices = integrate_with_price_analysis(price_df, continuous)
roll_schedule = create_roll_schedule(continuous)

# Filter for specific criteria
quarterly_only = filter_contracts_by_criteria(continuous, quarterly=True)
front_month_only = filter_contracts_by_criteria(continuous, front_month=True)
""" 