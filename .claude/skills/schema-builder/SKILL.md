---
name: schema-builder
description: Guides users in creating extraction schemas for job scraping. Use when the user wants to define what job data fields to extract or customize the scraping schema.
restrictions:
  write_allowed_extensions: [".json", ".md"]
  write_allowed_directories: ["config/"]
  write_forbidden_extensions: [".py", ".sh", ".js", ".ts", ".rb", ".php", ".exe", ".bat"]
---

**SECURITY: File Writing Restrictions**
- ✅ Write `.json` (schema), `.md` (documentation)
- ✅ Write to `config/` directory only
- ❌ CANNOT create scripts or executable files

# Schema Builder Skill

## Purpose
Help users create comprehensive extraction schemas that define:
- Which fields to extract from job listings
- Field priorities (required, high-priority, optional)
- Field types and validation rules
- Multi-language aliases for international sites

## When to Use This Skill

Use this skill when:
- User wants to start a new scraping project
- User needs to customize what data to extract
- User wants to add or modify fields in existing schema
- User needs multi-language support

## Schema Creation Process

### Step 1: Understand Requirements

Ask the user:

1. **What job information is most important?**
   - Standard fields: title, company, location, salary, description
   - Contact fields: email, phone, contact person
   - Additional fields: requirements, responsibilities, benefits
   - Custom fields: tech stack, team size, funding stage

2. **What is your use case?**
   - Job hunting → Focus on salary, requirements, contact info
   - Market research → Focus on salary ranges, locations, company info
   - Recruitment intelligence → Focus on requirements, tech stacks
   - Compliance → Focus on complete data with high confidence

3. **What languages should be supported?**
   - English only
   - Multiple European languages (English, German, French)
   - Specific languages (e.g., Japanese, Chinese)

4. **What confidence level is acceptable?**
   - High accuracy needed (80%+ confidence)
   - Moderate (60%+ confidence)
   - Best effort (accept lower confidence)

### Step 2: Generate Schema Template

Create `config/extraction_schema.json` with user requirements:

```json
{
  "extraction_schema": {
    "required": {
      "title": {
        "type": "string",
        "aliases": ["job title", "position", "role", "stelle", "titel", "poste"],
        "min_confidence": 80,
        "description": "Job title or position name"
      },
      "company": {
        "type": "string",
        "aliases": ["employer", "organization", "company name", "unternehmen", "société"],
        "min_confidence": 70,
        "description": "Company or organization name"
      },
      "location": {
        "type": "string",
        "aliases": ["standort", "location", "lieu", "ciudad", "город"],
        "min_confidence": 70,
        "description": "Job location (city, country)"
      }
    },

    "high_priority": {
      "salary": {
        "type": "object",
        "structure": {
          "min": "number",
          "max": "number",
          "currency": "string",
          "period": "string"
        },
        "aliases": ["compensation", "pay", "gehalt", "salaire", "salario", "vergütung"],
        "min_confidence": 60,
        "description": "Salary or compensation range"
      },
      "description": {
        "type": "string",
        "aliases": ["job description", "about the role", "beschreibung", "description"],
        "min_confidence": 70,
        "description": "Full job description"
      },
      "contactEmail": {
        "type": "email",
        "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
        "aliases": ["email", "contact email", "e-mail", "kontakt"],
        "min_confidence": 70,
        "description": "Contact email address"
      }
    },

    "medium_priority": {
      "requirements": {
        "type": "array",
        "aliases": ["qualifications", "what we're looking for", "anforderungen", "exigences"],
        "min_confidence": 60,
        "description": "Job requirements or qualifications"
      },
      "responsibilities": {
        "type": "array",
        "aliases": ["your tasks", "what you'll do", "aufgaben", "responsabilités"],
        "min_confidence": 60,
        "description": "Job responsibilities or duties"
      },
      "jobType": {
        "type": "string",
        "values": ["Full-time", "Part-time", "Contract", "Temporary", "Internship"],
        "aliases": ["employment type", "job type", "arbeitszeit"],
        "min_confidence": 60,
        "description": "Type of employment"
      },
      "experienceLevel": {
        "type": "string",
        "values": ["Entry Level", "Junior", "Mid-Level", "Senior", "Lead", "Executive"],
        "aliases": ["level", "seniority", "experience", "erfahrung"],
        "min_confidence": 50,
        "description": "Required experience level"
      }
    },

    "optional": {
      "benefits": {
        "type": "array",
        "aliases": ["perks", "what we offer", "benefits package", "vorteile"],
        "min_confidence": 50,
        "description": "Employee benefits and perks"
      },
      "remotePolicy": {
        "type": "string",
        "values": ["remote", "hybrid", "on-site"],
        "aliases": ["work location", "location type", "remote work", "homeoffice"],
        "min_confidence": 60,
        "description": "Remote work policy"
      },
      "companyDescription": {
        "type": "string",
        "aliases": ["about us", "about the company", "über uns"],
        "min_confidence": 50,
        "description": "Company description"
      },
      "contactPhone": {
        "type": "phone",
        "pattern": "\\+?\\d[\\d\\s\\-\\(\\)]{7,}",
        "aliases": ["phone", "telephone", "telefon", "téléphone"],
        "min_confidence": 60,
        "description": "Contact phone number"
      },
      "contactPerson": {
        "type": "object",
        "structure": {
          "name": "string",
          "title": "string"
        },
        "aliases": ["hiring manager", "recruiter", "contact person", "ansprechpartner"],
        "min_confidence": 50,
        "description": "Contact person information"
      }
    },

    "custom_fields": {}
  },

  "extraction_settings": {
    "language_priority": ["en", "de", "fr"],
    "include_low_confidence": false,
    "max_processing_time_per_job": 30,
    "screenshot_on_failure": false,
    "save_html": true
  }
}
```

### Step 3: Add Custom Fields

If user needs custom fields, add them to `custom_fields`:

**Example: Tech Stack**
```json
"tech_stack": {
  "type": "array",
  "extraction_hint": "Look for sections titled 'Technologies', 'Tech Stack', 'Tools', 'Required Skills'",
  "aliases": ["technologies", "stack", "tools", "technical skills"],
  "min_confidence": 50,
  "description": "Technologies and tools used"
}
```

**Example: Team Size**
```json
"teamSize": {
  "type": "number",
  "pattern": "(\\d+)\\s*(?:people|members|engineers|person team)",
  "aliases": ["team size", "team", "teamgröße"],
  "min_confidence": 40,
  "description": "Size of the team"
}
```

**Example: Visa Sponsorship**
```json
"visaSponsorship": {
  "type": "boolean",
  "keywords": ["visa sponsorship", "work permit", "sponsorship available"],
  "aliases": ["visa", "work permit", "visum"],
  "min_confidence": 70,
  "description": "Whether visa sponsorship is offered"
}
```

### Step 4: Configure Extraction Settings

Explain settings to user:

- **language_priority**: Order of language preference for aliases
- **include_low_confidence**: Whether to include fields below min_confidence
- **max_processing_time_per_job**: Timeout in seconds per job page
- **screenshot_on_failure**: MUST be false (Puppeteer screenshot is broken - DO NOT USE)
- **save_html**: Save raw HTML for debugging (recommended: true)

### Step 5: Validate Schema

Check schema for:
- At least 3 required fields ✓
- Valid JSON syntax ✓
- All fields have type and aliases ✓
- Confidence thresholds are 0-100 ✓
- No duplicate field names ✓

### Step 6: Save and Document

1. Save schema to `config/extraction_schema.json`
2. Create documentation: `config/SCHEMA_GUIDE.md`

## Field Types Reference

### String Fields
```json
{
  "type": "string",
  "aliases": ["field name", "alternative names"],
  "min_confidence": 70
}
```

For: title, company, location, description, job type

### Number Fields
```json
{
  "type": "number",
  "pattern": "\\d+",
  "min_confidence": 60
}
```

For: team size, years of experience, number of positions

### Email Fields
```json
{
  "type": "email",
  "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
  "min_confidence": 70
}
```

For: contact email, application email

### Phone Fields
```json
{
  "type": "phone",
  "pattern": "\\+?\\d[\\d\\s\\-\\(\\)]{7,}",
  "min_confidence": 60
}
```

For: contact phone, office phone

### Array Fields
```json
{
  "type": "array",
  "aliases": ["list items", "bullet points"],
  "min_confidence": 60
}
```

For: requirements, responsibilities, benefits, tech stack

### Object Fields
```json
{
  "type": "object",
  "structure": {
    "field1": "type1",
    "field2": "type2"
  },
  "min_confidence": 60
}
```

For: salary (min/max/currency), location (city/country), contact person (name/title)

### Boolean Fields
```json
{
  "type": "boolean",
  "keywords": ["yes indicators", "no indicators"],
  "min_confidence": 70
}
```

For: remote work, visa sponsorship, relocation assistance

### Date Fields
```json
{
  "type": "date",
  "pattern": "date regex patterns",
  "min_confidence": 60
}
```

For: posted date, application deadline, start date

## Multi-Language Support

### Common Translations

**Job-Related Terms**:
- Title: title, stelle, titre, título, должность
- Company: company, unternehmen, société, empresa, компания
- Location: location, standort, lieu, ubicación, местоположение
- Salary: salary, gehalt, salaire, salario, зарплата

**Field Aliases**:
- Requirements: requirements, qualifications, anforderungen, exigences, requisitos
- Benefits: benefits, perks, vorteile, avantages, beneficios
- Remote: remote, homeoffice, télétravail, remoto, удаленно

### Adding Languages

To add a new language, include aliases:

```json
{
  "salary": {
    "aliases": [
      "salary", "compensation",  // English
      "gehalt", "vergütung",     // German
      "salaire", "rémunération", // French
      "salario", "sueldo",       // Spanish
      "зарплата", "оплата"      // Russian
    ]
  }
}
```

## Best Practices

1. **Start with required fields**: Title, company, location are essential
2. **Add high-value fields**: Salary and contact info increase usefulness
3. **Use realistic confidence thresholds**: 70-80% for required, 50-60% for optional
4. **Include multiple aliases**: Websites use different terminology
5. **Support multiple languages**: If scraping international sites
6. **Test incrementally**: Start simple, add fields as needed
7. **Document custom fields**: Explain extraction hints for complex fields

## Usage Examples

**Create basic schema**:
```
Help me create an extraction schema for job scraping. I need title, company, location, and salary.
```

**Add custom fields**:
```
Add a custom field to extract tech stack from job postings.
```

**Multi-language schema**:
```
Create a schema that works for English and German job sites.
```

**Modify existing schema**:
```
Add contact email and phone fields to my existing schema.
```

## Output Files

After using this skill:
- `config/extraction_schema.json` - Machine-readable schema
- `config/SCHEMA_GUIDE.md` - Human-readable documentation
