from typing import Dict, Any, List, Tuple


# Measurement rules in inches. Frontend multiplies by 2.54 if unit is 'cm'.
MEASUREMENT_RULES = {
    'shirtLength': {
        'min': 20,
        'max': 60,
        'hint': 'High shoulder point to desired hem',
        'example': '40'
    },
    'bust': {
        'min': 28,
        'max': 60,
        'hint': 'Around the fullest part of the bust',
        'example': '36'
    },
    'shoulder': {
        'min': 11,
        'max': 22,
        'hint': 'Seam to seam across the upper back',
        'example': '14'
    },
    'waist': {
        'min': 22,
        'max': 55,
        'hint': 'Around the natural waistline',
        'example': '30'
    },
    'hips': {
        'min': 28,
        'max': 60,
        'hint': 'Around the fullest part of the hips',
        'example': '38'
    },
    'sleeveLength': {
        'min': 6,
        'max': 30,
        'hint': 'Shoulder seam to wrist',
        'example': '23'
    },
    'armhole': {
        'min': 12,
        'max': 28,
        'hint': 'Around the arm at the shoulder joint',
        'example': '17'
    },
}


def validate_measurements(measurements: Dict[str, Any], unit: str) -> Tuple[bool, List[str]]:
    """
    Validates a measurement dictionary against MEASUREMENT_RULES.
    
    Args:
        measurements: Dict with keys like 'shirtLength', 'bust', etc.
        unit: 'inches' or 'cm'
    
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    required_fields = list(MEASUREMENT_RULES.keys())
    
    # Check for missing required fields
    for field in required_fields:
        if field not in measurements or measurements[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate ranges
    multiplier = 2.54 if unit == 'cm' else 1.0
    
    for field, value in measurements.items():
        if field not in MEASUREMENT_RULES:
            continue  # Ignore 'specialNotes' or unknown fields
        
        if not isinstance(value, (int, float)):
            errors.append(f"{field}: Must be a number")
            continue
        
        rule = MEASUREMENT_RULES[field]
        
        # Convert input to inches for validation against base rules
        value_in_inches = value / multiplier if unit == 'cm' else value
        
        if not (rule['min'] <= value_in_inches <= rule['max']):
            errors.append(
                f"{field}: Must be between {rule['min']} and {rule['max']} inches "
                f"({rule['min'] * multiplier:.1f}–{rule['max'] * multiplier:.1f} {unit})"
            )
    
    return len(errors) == 0, errors