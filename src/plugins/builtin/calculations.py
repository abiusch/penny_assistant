"""
Calculations plugin for PennyGPT
"""

import re
import math
from typing import Dict, Any, Optional, List
from ..base_plugin import BasePlugin


class CalculationsPlugin(BasePlugin):
    """Plugin to handle mathematical calculations and unit conversions"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_precision = self.config.get('max_precision', 6)
    
    def can_handle(self, intent: str, query: str) -> bool:
        """Check if this plugin can handle calculation requests"""
        if intent in ['calculation', 'math', 'convert']:
            return True
            
        query_lower = query.lower().strip()
        
        # Math operation patterns
        math_patterns = [
            r'what[\'s]?\s+(is\s+)?(\d+[\.\d]*\s*[\+\-\*\/x]\s*\d+[\.\d]*)',
            r'calculate\s+',
            r'compute\s+',
            r'\d+\s*[\+\-\*\/x]\s*\d+',
            r'(\d+[\.\d]*)\s*percent\s*of\s*(\d+[\.\d]*)',
            r'what[\'s]?\s+(\d+[\.\d]*)\s*%\s*of\s*(\d+[\.\d]*)',
            r'square\s+root\s+of\s+(\d+[\.\d]*)',
            r'sqrt\s*\(\s*(\d+[\.\d]*)\s*\)',
            r'(\d+[\.\d]*)\s*squared',
            r'(\d+[\.\d]*)\s*to\s+the\s+power\s+of\s+(\d+[\.\d]*)',
        ]
        
        # Unit conversion patterns
        conversion_patterns = [
            r'convert\s+(\d+[\.\d]*)\s*(\w+)\s+to\s+(\w+)',
            r'(\d+[\.\d]*)\s*(celsius|fahrenheit|kelvin)\s+to\s+(celsius|fahrenheit|kelvin)',
            r'(\d+[\.\d]*)\s*(feet|meters|inches|cm|miles|km)\s+to\s+(feet|meters|inches|cm|miles|km)',
            r'(\d+[\.\d]*)\s*(pounds|kg|grams|ounces)\s+to\s+(pounds|kg|grams|ounces)',
        ]
        
        all_patterns = math_patterns + conversion_patterns
        return any(re.search(pattern, query_lower) for pattern in all_patterns)
    
    async def execute(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute calculation or conversion"""
        try:
            result = self._parse_and_calculate(query)
            
            if result:
                return {
                    'success': True,
                    'response': result['response'],
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'response': "I couldn't understand that calculation. Try something like 'What's 15 plus 25?' or 'Convert 25 celsius to fahrenheit'.",
                    'error': 'calculation_not_recognized'
                }
                
        except Exception as e:
            return {
                'success': False,
                'response': f"Error performing calculation: {str(e)}",
                'error': str(e)
            }
    
    def _parse_and_calculate(self, query: str) -> Optional[Dict[str, Any]]:
        """Parse query and perform calculation"""
        query_lower = query.lower().strip()
        
        # Try basic arithmetic first
        arithmetic_result = self._handle_arithmetic(query_lower)
        if arithmetic_result:
            return arithmetic_result
        
        # Try percentage calculations
        percentage_result = self._handle_percentage(query_lower)
        if percentage_result:
            return percentage_result
        
        # Try unit conversions
        conversion_result = self._handle_conversions(query_lower)
        if conversion_result:
            return conversion_result
        
        # Try advanced math functions
        math_result = self._handle_advanced_math(query_lower)
        if math_result:
            return math_result
        
        return None
    
    def _handle_arithmetic(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle basic arithmetic operations"""
        # Pattern for operations like "15 + 25", "what's 10 * 3"
        patterns = [
            r'what[\'s]?\s+(?:is\s+)?(\d+(?:\.\d+)?)\s*([\+\-\*\/x])\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*([\+\-\*\/x])\s*(\d+(?:\.\d+)?)',
            r'calculate\s+(\d+(?:\.\d+)?)\s*([\+\-\*\/x])\s*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    num1 = float(match.group(1))
                    operator = match.group(2)
                    num2 = float(match.group(3))
                    
                    if operator in ['+', 'plus']:
                        result = num1 + num2
                        operation = f"{num1} + {num2}"
                    elif operator in ['-', 'minus']:
                        result = num1 - num2
                        operation = f"{num1} - {num2}"
                    elif operator in ['*', 'x', 'times']:
                        result = num1 * num2
                        operation = f"{num1} × {num2}"
                    elif operator in ['/', 'divided by']:
                        if num2 == 0:
                            return {
                                'response': "Cannot divide by zero!",
                                'operation': f"{num1} ÷ 0",
                                'error': 'division_by_zero'
                            }
                        result = num1 / num2
                        operation = f"{num1} ÷ {num2}"
                    else:
                        continue
                    
                    formatted_result = self._format_number(result)
                    return {
                        'response': f"{operation} equals {formatted_result}",
                        'operation': operation,
                        'result': result,
                        'formatted_result': formatted_result
                    }
                except ValueError:
                    continue
        
        return None
    
    def _handle_percentage(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle percentage calculations"""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*percent\s*of\s*(\d+(?:\.\d+)?)',
            r'what[\'s]?\s+(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    percentage = float(match.group(1))
                    total = float(match.group(2))
                    result = (percentage / 100) * total
                    
                    formatted_result = self._format_number(result)
                    return {
                        'response': f"{percentage}% of {total} is {formatted_result}",
                        'operation': f"{percentage}% of {total}",
                        'result': result,
                        'formatted_result': formatted_result
                    }
                except ValueError:
                    continue
        
        return None
    
    def _handle_advanced_math(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle advanced math functions"""
        # Square root
        sqrt_patterns = [
            r'square\s+root\s+of\s+(\d+(?:\.\d+)?)',
            r'sqrt\s*\(\s*(\d+(?:\.\d+)?)\s*\)'
        ]
        
        for pattern in sqrt_patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    number = float(match.group(1))
                    if number < 0:
                        return {
                            'response': "Cannot calculate square root of negative number",
                            'operation': f"√{number}",
                            'error': 'negative_sqrt'
                        }
                    result = math.sqrt(number)
                    formatted_result = self._format_number(result)
                    return {
                        'response': f"The square root of {number} is {formatted_result}",
                        'operation': f"√{number}",
                        'result': result,
                        'formatted_result': formatted_result
                    }
                except ValueError:
                    continue
        
        # Squared
        squared_match = re.search(r'(\d+(?:\.\d+)?)\s*squared', query)
        if squared_match:
            try:
                number = float(squared_match.group(1))
                result = number ** 2
                formatted_result = self._format_number(result)
                return {
                    'response': f"{number} squared is {formatted_result}",
                    'operation': f"{number}²",
                    'result': result,
                    'formatted_result': formatted_result
                }
            except ValueError:
                pass
        
        # Power
        power_match = re.search(r'(\d+(?:\.\d+)?)\s+to\s+the\s+power\s+of\s+(\d+(?:\.\d+)?)', query)
        if power_match:
            try:
                base = float(power_match.group(1))
                exponent = float(power_match.group(2))
                result = base ** exponent
                formatted_result = self._format_number(result)
                return {
                    'response': f"{base} to the power of {exponent} is {formatted_result}",
                    'operation': f"{base}^{exponent}",
                    'result': result,
                    'formatted_result': formatted_result
                }
            except ValueError:
                pass
        
        return None
    
    def _handle_conversions(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle unit conversions"""
        # Temperature conversions
        temp_match = re.search(r'(\d+(?:\.\d+)?)\s*(celsius|fahrenheit|kelvin)\s+to\s+(celsius|fahrenheit|kelvin)', query)
        if temp_match:
            return self._convert_temperature(temp_match)
        
        # Length conversions
        length_match = re.search(r'(\d+(?:\.\d+)?)\s*(feet|meters|inches|cm|miles|km)\s+to\s+(feet|meters|inches|cm|miles|km)', query)
        if length_match:
            return self._convert_length(length_match)
        
        # Weight conversions
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(pounds|kg|grams|ounces)\s+to\s+(pounds|kg|grams|ounces)', query)
        if weight_match:
            return self._convert_weight(weight_match)
        
        return None
    
    def _convert_temperature(self, match) -> Dict[str, Any]:
        """Convert temperature units"""
        try:
            value = float(match.group(1))
            from_unit = match.group(2).lower()
            to_unit = match.group(3).lower()
            
            # Convert to Celsius first
            if from_unit == 'fahrenheit':
                celsius = (value - 32) * 5/9
            elif from_unit == 'kelvin':
                celsius = value - 273.15
            else:  # celsius
                celsius = value
            
            # Convert from Celsius to target
            if to_unit == 'fahrenheit':
                result = celsius * 9/5 + 32
            elif to_unit == 'kelvin':
                result = celsius + 273.15
            else:  # celsius
                result = celsius
            
            formatted_result = self._format_number(result)
            return {
                'response': f"{value}° {from_unit.title()} is {formatted_result}° {to_unit.title()}",
                'operation': f"{value}° {from_unit} → {to_unit}",
                'result': result,
                'formatted_result': formatted_result,
                'conversion_type': 'temperature'
            }
        except ValueError:
            return {'response': "Invalid temperature conversion", 'error': 'invalid_conversion'}
    
    def _convert_length(self, match) -> Dict[str, Any]:
        """Convert length units"""
        try:
            value = float(match.group(1))
            from_unit = match.group(2).lower()
            to_unit = match.group(3).lower()
            
            # Conversion factors to meters
            to_meters = {
                'meters': 1, 'feet': 0.3048, 'inches': 0.0254,
                'cm': 0.01, 'miles': 1609.34, 'km': 1000
            }
            
            # Convert to meters, then to target unit
            meters = value * to_meters[from_unit]
            result = meters / to_meters[to_unit]
            
            formatted_result = self._format_number(result)
            return {
                'response': f"{value} {from_unit} is {formatted_result} {to_unit}",
                'operation': f"{value} {from_unit} → {to_unit}",
                'result': result,
                'formatted_result': formatted_result,
                'conversion_type': 'length'
            }
        except (ValueError, KeyError):
            return {'response': "Invalid length conversion", 'error': 'invalid_conversion'}
    
    def _convert_weight(self, match) -> Dict[str, Any]:
        """Convert weight units"""
        try:
            value = float(match.group(1))
            from_unit = match.group(2).lower()
            to_unit = match.group(3).lower()
            
            # Conversion factors to grams
            to_grams = {
                'grams': 1, 'kg': 1000, 'pounds': 453.592, 'ounces': 28.3495
            }
            
            # Convert to grams, then to target unit
            grams = value * to_grams[from_unit]
            result = grams / to_grams[to_unit]
            
            formatted_result = self._format_number(result)
            return {
                'response': f"{value} {from_unit} is {formatted_result} {to_unit}",
                'operation': f"{value} {from_unit} → {to_unit}",
                'result': result,
                'formatted_result': formatted_result,
                'conversion_type': 'weight'
            }
        except (ValueError, KeyError):
            return {'response': "Invalid weight conversion", 'error': 'invalid_conversion'}
    
    def _format_number(self, number: float) -> str:
        """Format number for display"""
        if number == int(number):
            return str(int(number))
        else:
            # Round to max_precision decimal places, then remove trailing zeros
            formatted = f"{number:.{self.max_precision}f}".rstrip('0').rstrip('.')
            return formatted if formatted else '0'
    
    def get_help_text(self) -> str:
        return "Ask me to calculate! Try: 'What's 15 + 25?', '20% of 100', or 'Convert 25 celsius to fahrenheit'"
    
    def get_supported_intents(self) -> List[str]:
        return ['calculation', 'math', 'convert']


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test_calculations():
        plugin = CalculationsPlugin()
        
        test_queries = [
            "What's 15 + 25?",
            "25% of 200",
            "Square root of 144",
            "Convert 25 celsius to fahrenheit",
            "10 * 5"
        ]
        
        for query in test_queries:
            print(f"\nTesting: {query}")
            result = await plugin.execute(query)
            print(f"Result: {result['response']}")
    
    asyncio.run(test_calculations())
