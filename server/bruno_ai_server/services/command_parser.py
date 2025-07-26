"""
Command parser for processing voice commands and extracting pantry actions.

This service handles:
- Natural language processing of voice commands
- Intent detection (add/edit/delete pantry items)
- Entity extraction (food items, quantities, units, dates)
- Command validation and structure creation
- Support for multiple command patterns
"""

import re
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PantryAction(Enum):
    """Types of pantry actions that can be performed."""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    REMOVE = "remove"
    LIST = "list"
    SEARCH = "search"
    CHECK = "check"
    INCREMENT = "increment"
    DECREMENT = "decrement"
    USE = "use"
    SET_QUANTITY = "set_quantity"


@dataclass
class ParsedEntity:
    """A parsed entity from voice command (food item, quantity, etc.)"""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    expiration_date: Optional[date] = None
    confidence: float = 1.0


@dataclass
class CommandResult:
    """Result of command parsing."""
    action: PantryAction
    entities: List[ParsedEntity]
    raw_text: str
    confidence: float
    errors: List[str] = None
    metadata: Dict[str, Any] = None


class CommandParser:
    """
    Natural language command parser for pantry voice commands.
    
    Supports patterns like:
    - "Add milk to the pantry"
    - "I bought 2 pounds of chicken"
    - "Remove expired bread"
    - "Update the milk quantity to 1 gallon"
    - "What's in my fridge?"
    """
    
    def __init__(self):
        """Initialize the command parser."""
        self._setup_patterns()
        self._setup_food_vocabulary()
        self._setup_units_vocabulary()
    
    def _setup_patterns(self):
        """Setup regex patterns for command matching."""
        
        # Action patterns (case-insensitive)
        self.action_patterns = {
            PantryAction.ADD: [
                r'(?:add|put|store|place|bought?|got|have)\s+(.+?)(?:\s+(?:to|in)\s+(?:the\s+)?(?:pantry|fridge|freezer))?',
                r'(?:i\s+)?(?:just\s+)?(?:bought?|got|picked\s+up|purchased)\s+(.+)',
                r'(?:can\s+you\s+)?(?:please\s+)?add\s+(.+?)(?:\s+to\s+(?:my\s+)?(?:pantry|fridge|freezer))?',
                r'(?:put\s+)?(.+?)\s+(?:goes?\s+)?(?:in|into)\s+(?:the\s+)?(?:pantry|fridge|freezer)',
            ],
            PantryAction.UPDATE: [
                r'(?:update|change|modify|edit)\s+(?:the\s+)?(.+?)(?:\s+(?:to|with))?',
                r'(?:set|make)\s+(?:the\s+)?(.+?)\s+(?:to|as)\s+(.+)',
                r'(?:change|update)\s+(.+?)\s+(?:quantity|amount)\s+to\s+(.+)',
            ],
            PantryAction.DELETE: [
                r'(?:delete|remove|throw\s+(?:away|out)|discard|get\s+rid\s+of)\s+(?:the\s+)?(.+)',
                r'(?:i\s+)?(?:used\s+up|finished|ran\s+out\s+of)\s+(?:the\s+)?(.+)',
                r'(?:expired|bad|spoiled)\s+(.+)',
            ],
            PantryAction.LIST: [
                r'(?:what(?:\'s|\s+is)|show\s+me|list)\s+(?:in\s+)?(?:my\s+)?(?:pantry|fridge|freezer)',
                r'(?:what\s+do\s+i\s+have)\s+(?:in\s+(?:my\s+)?(?:pantry|fridge|freezer))?',
                r'(?:show|list)\s+(?:all\s+)?(?:my\s+)?(?:food|items|groceries)',
            ],
            PantryAction.SEARCH: [
                r'(?:do\s+i\s+have|find|search\s+for|look\s+for)\s+(.+)',
                r'(?:is\s+there|are\s+there)\s+(?:any\s+)?(.+?)(?:\s+in\s+(?:my\s+)?(?:pantry|fridge|freezer))?',
            ],
            PantryAction.CHECK: [
                r'(?:check|when\s+(?:does|do)|how\s+much)\s+(.+?)(?:\s+(?:expire|expires?|expir))?',
                r'(?:what(?:\'s|\s+is)\s+(?:the\s+)?(?:expiration|expiry)\s+(?:date\s+)?(?:of|for))\s+(.+)',
            ],
            PantryAction.INCREMENT: [
                r'(?:add|increase|increment)\s+(.+?)\s+(?:to|of)\s+(.+)',
                r'(?:more|additional)\s+(.+)',
                r'(?:bought|got|picked\s+up)\s+(?:more|additional)\s+(.+)',
            ],
            PantryAction.DECREMENT: [
                r'(?:subtract|decrease|decrement|remove)\s+(.+?)\s+(?:from|of)\s+(.+)',
                r'(?:less|fewer)\s+(.+)',
            ],
            PantryAction.USE: [
                r'(?:use|used)\s+(.+)',
                r'(?:i\s+)?(?:used|consumed|ate|drank)\s+(.+)',
                r'(?:cooking\s+with|making\s+with)\s+(.+)',
            ],
            PantryAction.SET_QUANTITY: [
                r'(?:set|make)\s+(?:the\s+)?(.+?)\s+(?:to|at)\s+(.+)',
                r'(?:change|update)\s+(?:the\s+)?(.+?)\s+(?:quantity|amount)\s+to\s+(.+)',
                r'(?:i\s+have|there\s+are?)\s+(.+?)\s+(?:of\s+)?(.+?)\s+(?:left|remaining)',
            ]
        }
    
    def _setup_food_vocabulary(self):
        """Setup vocabulary for common food items and categories."""
        self.food_categories = {
            'dairy': ['milk', 'cheese', 'butter', 'yogurt', 'cream', 'sour cream'],
            'meat': ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'salmon'],
            'vegetables': ['carrot', 'onion', 'tomato', 'potato', 'lettuce', 'spinach', 'broccoli'],
            'fruits': ['apple', 'banana', 'orange', 'grape', 'strawberry', 'lemon', 'lime'],
            'grains': ['bread', 'rice', 'pasta', 'cereal', 'oats', 'quinoa', 'flour'],
            'pantry': ['salt', 'pepper', 'sugar', 'oil', 'vinegar', 'sauce', 'spice']
        }
        
        # Flatten for quick lookup
        self.all_foods = set()
        for category_foods in self.food_categories.values():
            self.all_foods.update(category_foods)
    
    def _setup_units_vocabulary(self):
        """Setup vocabulary for units and measurements."""
        self.unit_patterns = {
            # Volume
            'cup': ['cup', 'cups', 'c'],
            'tablespoon': ['tablespoon', 'tablespoons', 'tbsp', 'tbs'],
            'teaspoon': ['teaspoon', 'teaspoons', 'tsp'],
            'liter': ['liter', 'liters', 'l', 'litre', 'litres'],
            'milliliter': ['milliliter', 'milliliters', 'ml'],
            'gallon': ['gallon', 'gallons', 'gal'],
            'quart': ['quart', 'quarts', 'qt'],
            'pint': ['pint', 'pints', 'pt'],
            'fluid_ounce': ['fluid ounce', 'fluid ounces', 'fl oz', 'floz'],
            
            # Weight
            'pound': ['pound', 'pounds', 'lb', 'lbs'],
            'ounce': ['ounce', 'ounces', 'oz'],
            'gram': ['gram', 'grams', 'g'],
            'kilogram': ['kilogram', 'kilograms', 'kg'],
            
            # Count
            'piece': ['piece', 'pieces', 'pc', 'pcs', 'each'],
            'dozen': ['dozen', 'doz'],
            'pack': ['pack', 'packs', 'package', 'packages'],
            'box': ['box', 'boxes'],
            'can': ['can', 'cans'],
            'jar': ['jar', 'jars'],
            'bottle': ['bottle', 'bottles']
        }
        
        # Create reverse lookup for units
        self.unit_lookup = {}
        for standard_unit, variations in self.unit_patterns.items():
            for variation in variations:
                self.unit_lookup[variation.lower()] = standard_unit
    
    def parse_command(self, text: str) -> CommandResult:
        """
        Parse a voice command and extract structured pantry actions.
        
        Args:
            text: The transcribed voice command text
            
        Returns:
            CommandResult with parsed action and entities
        """
        if not text or not text.strip():
            return CommandResult(
                action=PantryAction.LIST,
                entities=[],
                raw_text=text,
                confidence=0.0,
                errors=["Empty command text"]
            )
        
        text = text.strip().lower()
        logger.info(f"Parsing command: '{text}'")
        
        # Try to match action patterns
        action, match_confidence, matched_groups = self._detect_action(text)
        
        if action is None:
            # Default to ADD if we detect food items but no clear action
            if self._contains_food_items(text):
                action = PantryAction.ADD
                match_confidence = 0.6
                matched_groups = [text]  # Use entire text
            else:
                action = PantryAction.LIST
                match_confidence = 0.3
                matched_groups = []
        
        # Extract entities from matched groups
        entities = []
        errors = []
        
        if matched_groups:
            for group in matched_groups:
                if group and group.strip():
                    parsed_entities = self._extract_entities(group.strip(), action)
                    entities.extend(parsed_entities)
        
        # Calculate overall confidence
        entity_confidence = sum(e.confidence for e in entities) / len(entities) if entities else 0.5
        overall_confidence = (match_confidence + entity_confidence) / 2
        
        # Validate the result
        if action in [PantryAction.ADD, PantryAction.UPDATE, PantryAction.DELETE] and not entities:
            errors.append(f"No items identified for {action.value} action")
            overall_confidence *= 0.5
        
        return CommandResult(
            action=action,
            entities=entities,
            raw_text=text,
            confidence=overall_confidence,
            errors=errors if errors else None,
            metadata={
                "matched_groups": matched_groups,
                "action_confidence": match_confidence,
                "entity_confidence": entity_confidence
            }
        )
    
    def _detect_action(self, text: str) -> Tuple[Optional[PantryAction], float, List[str]]:
        """
        Detect the primary action from the command text.
        
        Returns:
            Tuple of (action, confidence, matched_groups)
        """
        best_action = None
        best_confidence = 0.0
        best_groups = []
        
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = 0.9  # High confidence for explicit pattern match
                    groups = [g for g in match.groups() if g]
                    
                    # Boost confidence if pattern is more specific
                    if len(pattern) > 50:  # More specific patterns
                        confidence += 0.05
                    
                    if confidence > best_confidence:
                        best_action = action
                        best_confidence = confidence
                        best_groups = groups
        
        return best_action, best_confidence, best_groups
    
    def _contains_food_items(self, text: str) -> bool:
        """Check if text contains recognizable food items."""
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        return len(text_words.intersection(self.all_foods)) > 0
    
    def _extract_entities(self, text: str, action: PantryAction) -> List[ParsedEntity]:
        """
        Extract food entities from text.
        
        Args:
            text: Text to parse for entities
            action: The detected action (helps with context)
            
        Returns:
            List of ParsedEntity objects
        """
        entities = []
        
        # Split text by common separators to handle multiple items
        item_texts = re.split(r'[,;]\s*|\s+and\s+', text)
        
        for item_text in item_texts:
            entity = self._parse_single_entity(item_text.strip())
            if entity:
                entities.append(entity)
        
        return entities
    
    def _parse_single_entity(self, text: str) -> Optional[ParsedEntity]:
        """
        Parse a single food entity with quantity, unit, etc.
        
        Args:
            text: Text describing a single food item
            
        Returns:
            ParsedEntity or None if parsing fails
        """
        if not text:
            return None
        
        # Extract quantity and unit
        quantity, unit, remaining_text = self._extract_quantity_unit(text)
        
        # Extract expiration/date information
        expiration_date, remaining_text = self._extract_date(remaining_text)
        
        # Extract location information
        location, remaining_text = self._extract_location(remaining_text)
        
        # What's left should be the food item name
        food_name = self._clean_food_name(remaining_text)
        
        if not food_name:
            return None
        
        # Calculate confidence based on how well we parsed everything
        confidence = 0.7  # Base confidence
        
        if quantity is not None:
            confidence += 0.1
        if unit is not None:
            confidence += 0.1
        if food_name.lower() in self.all_foods:
            confidence += 0.1
        
        return ParsedEntity(
            name=food_name,
            quantity=quantity,
            unit=unit,
            location=location,
            expiration_date=expiration_date,
            confidence=min(1.0, confidence)
        )
    
    def _extract_quantity_unit(self, text: str) -> Tuple[Optional[float], Optional[str], str]:
        """Extract quantity and unit from text."""
        # Pattern for number + unit
        pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)'
        matches = re.findall(pattern, text)
        
        quantity = None
        unit = None
        remaining_text = text
        
        for qty_str, unit_str in matches:
            # Check if unit is valid
            if unit_str.lower() in self.unit_lookup:
                quantity = float(qty_str)
                unit = self.unit_lookup[unit_str.lower()]
                # Remove the matched quantity+unit from text
                remaining_text = re.sub(f'{qty_str}\\s*{unit_str}', '', remaining_text, flags=re.IGNORECASE)
                break
        
        # Try to extract just numbers if no unit found
        if quantity is None:
            number_match = re.search(r'(\d+(?:\.\d+)?)', text)
            if number_match:
                quantity = float(number_match.group(1))
                remaining_text = re.sub(number_match.group(1), '', remaining_text)
        
        return quantity, unit, remaining_text.strip()
    
    def _extract_date(self, text: str) -> Tuple[Optional[date], str]:
        """Extract expiration date from text."""
        expiration_date = None
        remaining_text = text
        
        # Patterns for date extraction
        date_patterns = [
            r'(?:expires?|expiring|expiration)\s+(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:expires?|expiring|expiration)\s+(?:on\s+)?(?:in\s+)?(\d+)\s+days?',
            r'(?:best\s+by|use\s+by|good\s+until)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Just date format
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                
                # Try to parse the date
                try:
                    if date_str.isdigit():  # Number of days
                        days = int(date_str)
                        expiration_date = date.today() + timedelta(days=days)
                    else:  # Date format
                        # Try different date formats
                        for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                            try:
                                expiration_date = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                    
                    if expiration_date:
                        remaining_text = re.sub(pattern, '', remaining_text, flags=re.IGNORECASE)
                        break
                        
                except ValueError:
                    pass
        
        return expiration_date, remaining_text.strip()
    
    def _extract_location(self, text: str) -> Tuple[Optional[str], str]:
        """Extract storage location from text."""
        location = None
        remaining_text = text
        
        location_patterns = {
            'pantry': r'\b(?:pantry|cupboard|cabinet)\b',
            'fridge': r'\b(?:fridge|refrigerator|cooler)\b',
            'freezer': r'\b(?:freezer|frozen)\b',
            'counter': r'\b(?:counter|countertop)\b',
        }
        
        for loc, pattern in location_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                location = loc
                remaining_text = re.sub(pattern, '', remaining_text, flags=re.IGNORECASE)
                break
        
        return location, remaining_text.strip()
    
    def _clean_food_name(self, text: str) -> str:
        """Clean and normalize food name."""
        # Remove common words that aren't part of the food name
        stopwords = ['the', 'a', 'an', 'some', 'of', 'to', 'in', 'for', 'with', 'by']
        
        words = text.split()
        cleaned_words = [w for w in words if w.lower() not in stopwords and w.strip()]
        
        return ' '.join(cleaned_words).strip()
    
    def get_supported_actions(self) -> List[str]:
        """Get list of supported action types."""
        return [action.value for action in PantryAction]
    
    def validate_command_result(self, result: CommandResult) -> bool:
        """
        Validate a parsed command result.
        
        Args:
            result: CommandResult to validate
            
        Returns:
            True if result is valid for execution
        """
        if result.confidence < 0.3:
            return False
        
        # Action-specific validation
        if result.action in [PantryAction.ADD, PantryAction.UPDATE, PantryAction.DELETE]:
            if not result.entities:
                return False
            
            # Check that entities have required fields
            for entity in result.entities:
                if not entity.name:
                    return False
        
        return True
