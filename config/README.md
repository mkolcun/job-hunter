# Configuration Directory

This directory contains configuration files for the job scraping system.

## Files

### extraction_schema.json
**Purpose**: Defines which job fields to extract and how to extract them.

**Setup**:
1. Copy `extraction_schema.example.json` to `extraction_schema.json`
2. Customize fields based on your needs
3. Or use the schema-builder skill: Ask Claude to help create a schema

**Structure**:
- `required`: Fields that must be extracted (title, company, location minimum)
- `high_priority`: Important fields (salary, description, contact email)
- `medium_priority`: Useful fields (requirements, responsibilities, job type)
- `optional`: Nice-to-have fields (benefits, remote policy, company description)
- `custom_fields`: Your own custom fields

**Field Configuration**:
```json
{
  "fieldName": {
    "type": "string|number|email|phone|array|object|date|boolean",
    "aliases": ["alternative names", "in different languages"],
    "min_confidence": 70,
    "description": "What this field represents"
  }
}
```

### hooks_config.json (optional)
**Purpose**: Configure which hooks are enabled and their settings.

**Setup**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/rate_limiter.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/validate_extraction.py"
          },
          {
            "type": "command",
            "command": "python3 .claude/hooks/progress_tracker.py"
          }
        ]
      }
    ]
  }
}
```

## Quick Start

1. **Create your schema**:
   ```bash
   cp config/extraction_schema.example.json config/extraction_schema.json
   ```

2. **Customize for your needs**:
   - Edit required fields
   - Add custom fields
   - Adjust confidence thresholds
   - Add language support

3. **Or use Claude to help**:
   ```
   Help me create an extraction schema for scraping German job sites
   ```

## Schema Best Practices

1. **Start simple**: Begin with required fields only (title, company, location)
2. **Add incrementally**: Add more fields as you test and refine
3. **Use realistic thresholds**: 70-80% for required, 50-60% for optional
4. **Multi-language support**: Add aliases for international sites
5. **Test and iterate**: Run small batches, analyze results, improve schema

## Field Types

### String
Simple text fields (title, company, location)

### Number
Numeric values (team size, years of experience)

### Email
Email addresses with validation

### Phone
Phone numbers with formatting

### Array
Lists (requirements, responsibilities, benefits)

### Object
Nested structures (salary with min/max/currency, contact person with name/title)

### Date
Date values with normalization

### Boolean
Yes/no values (visa sponsorship, remote work)

## Examples

### Minimal Schema (Job Hunting)
Required: title, company, location, salary, description, contactEmail

### Market Research Schema
Required: title, company, location, salary
Optional: jobType, experienceLevel, requirements, benefits

### Recruitment Intelligence
Required: title, company, location
High-priority: requirements, techStack, salary, experienceLevel
Optional: teamSize, companyDescription

### Compliance/Legal
Required: All fields with high confidence (80%+)
Settings: include_low_confidence: false, screenshot_on_failure: true
