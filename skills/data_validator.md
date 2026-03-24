---
name: data-validator
description: Validate data quality and structure
tools: [Read, Write]
---

# Data Validator Skill

This skill validates data by checking:
- Schema compliance
- Data types and formats
- Required fields presence
- Value ranges and constraints
- Consistency across related fields

## Validation Process

1. **Schema Check**: Verify all required fields exist
2. **Type Check**: Ensure data types match expectations
3. **Format Check**: Validate formats (dates, emails, URLs, etc.)
4. **Range Check**: Verify values are within acceptable ranges
5. **Consistency Check**: Check relationships between fields

## Output Format

Return validation results as:
```json
{
  "valid": true/false,
  "errors": ["error message 1", "error message 2"],
  "warnings": ["warning message 1"],
  "stats": {
    "total_items": 100,
    "valid_items": 95,
    "invalid_items": 5
  }
}
```
