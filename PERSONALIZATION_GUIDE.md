# Application Personalization Guide

Complete guide to the automated CV and cover letter personalization system.

## Overview

The personalization system creates customized application documents for each filtered job by:

1. **Researching** each company individually (website, products, culture, news)
2. **Personalizing** your CV template to highlight relevant experience
3. **Customizing** your cover letter to show genuine interest and fit
4. **Saving** everything organized by company with full research notes

**Key Features:**
- One job at a time (fresh agent context for each)
- Deep company research (mission, values, tech stack, recent news)
- Smart personalization (only edits marked sections)
- No batching or shortcuts (deterministic, bulletproof process)
- Full tracking and error recovery

## Quick Start

### Prerequisites

1. Filtered job database exists:
```bash
/filter
```

2. Your templates are ready:
- `user_docs/cv_template.md` - Your master CV
- `user_docs/cover_letter_template.md` - Your master cover letter

### Run Personalization

```bash
/personalize
```

The system will:
1. Load all filtered jobs (e.g., 47 jobs)
2. Ask for confirmation
3. Process each job one by one
4. Research company → Personalize docs → Save → Next job
5. Report completion with statistics

**Time:** 5-10 minutes per job (4-8 hours for 47 jobs)

## Template Setup

### CV Template Structure

Your CV template (`user_docs/cv_template.md`) contains **EDITABLE** sections:

```markdown
<!-- EDITABLE: professional_summary -->
<!-- INSTRUCTIONS: Tailor this 2-3 sentence summary... -->

[Your content here]

<!-- END EDITABLE -->
```

**What Gets Personalized:**
- Professional summary (emphasize relevant skills)
- Recent experience highlights (reorder by relevance)
- Technical skills (prioritize matching stack)
- Soft skills (align with culture)
- Featured projects (select most relevant)
- Certifications (prioritize relevant ones)

**What Stays the Same:**
- Name, contact info
- Work history structure
- Education
- Core experience descriptions

### Cover Letter Template Structure

Your cover letter template (`user_docs/cover_letter_template.md`) contains:

```markdown
<!-- EDITABLE: opening_paragraph -->
<!-- INSTRUCTIONS: Mention specific job title... -->

[Your content here]

<!-- END EDITABLE -->
```

**What Gets Personalized:**
- Recipient info (hiring manager name if found)
- Salutation (use name if found)
- Opening paragraph (reference company mission/news)
- Company fit paragraph (show you've researched them)
- Experience paragraph (match job requirements)
- Value proposition (address their specific needs)
- Closing (enthusiastic but professional)

## Personalization Process (Per Job)

### Phase 1: Company Research (60% of time)

The agent researches each company from scratch:

#### Primary Sources
1. **Company Website** (if available from job data)
   - Mission statement
   - Company values
   - Products and services
   - About us / Culture page
   - Tech blog (for tech stack hints)
   - News / Press releases
   - Careers / Team page

2. **Web Search** (fallback/supplemental)
   - "[Company] mission and values"
   - "[Company] products"
   - "[Company] tech stack"
   - "[Company] recent news"
   - "[Company] company culture"

3. **Job Posting Analysis**
   - Required skills and technologies
   - Key responsibilities
   - Team structure
   - Experience expectations
   - Soft skills mentioned

#### Research Output

Saved to `applications/[job_id]_[company]/company_research.json`:

```json
{
  "company_info": {
    "website": "https://techcorp.com",
    "industry": "Enterprise Software / SaaS",
    "mission": "To revolutionize enterprise communication...",
    "values": ["Innovation", "Customer Success", "Collaboration"],
    "products": ["AI Chat Platform", "Workflow Automation"],
    "tech_stack": ["Python", "React", "PostgreSQL", "AWS"],
    "recent_news": [
      "Series B funding $50M (March 2025)",
      "Launched new AI features (February 2025)"
    ]
  },
  "job_analysis": {
    "key_requirements": ["5+ years Python", "Microservices", "AWS"],
    "required_tech": ["Python", "FastAPI", "PostgreSQL"],
    "soft_skills": ["Leadership", "Mentoring"],
    "team": "Backend Team (5 people)"
  },
  "personalization_hooks": {
    "mission_alignment": "AI-powered communication matches ML experience",
    "tech_stack_overlap": ["Python", "AWS", "Docker"],
    "cultural_fit": "Remote-friendly matches preferences",
    "recent_news_to_mention": "Series B funding shows growth"
  }
}
```

### Phase 2: Cover Letter Personalization (25% of time)

#### Before Personalization
```markdown
Dear [Hiring Manager],

I am writing to express my strong interest in the [Job Title] position at
[Company Name]. [Generic statement about the role.]

What particularly draws me to [Company Name] is [generic interest].

With [X years] of experience, I have [generic skills].
```

#### After Personalization
```markdown
Dear Sarah Johnson, Engineering Manager,

I am writing to express my strong interest in the Senior Backend Developer
position at TechCorp Solutions Inc. I was particularly drawn to your mission
of revolutionizing enterprise communication through AI-powered tools, especially
after reading about your recent Series B funding and the launch of your new AI
features in February 2025.

What particularly draws me to TechCorp Solutions Inc. is your innovative approach
to combining AI with enterprise communication tools. I am especially impressed by
your recent launch of AI-powered features, which aligns perfectly with my 3 years
of experience building ML-enhanced systems at scale. Your commitment to continuous
learning and flat hierarchy resonates with my belief in collaborative, transparent
engineering cultures.

With 6 years of backend development experience, specializing in Python microservices
and AWS infrastructure, I have delivered scalable solutions for SaaS products serving
100k+ users. At DataCorp, I architected a microservices platform using Python, FastAPI,
and PostgreSQL—the same stack I noticed in your engineering blog—which reduced API
latency by 60% and supported 3x user growth.
```

**Personalization Elements Added:**
- ✅ Hiring manager name (if found)
- ✅ Exact job title
- ✅ Company mission reference
- ✅ Recent news (Series B, AI features)
- ✅ Specific products mentioned
- ✅ Tech stack match highlighted
- ✅ Company values alignment
- ✅ Quantifiable achievements relevant to their needs

### Phase 3: CV Personalization (10% of time)

#### Professional Summary

**Before:**
```
Experienced software developer with background in backend systems.
```

**After:**
```
Senior Backend Developer with 6 years of experience building scalable Python
microservices and cloud infrastructure. Specialized in AI-enhanced SaaS platforms,
with expertise in the AWS/Docker/Kubernetes stack. Passionate about clean
architecture, mentoring, and delivering customer-centric solutions aligned with
TechCorp's mission of revolutionizing enterprise communication.
```

#### Technical Skills Reordering

**Before:**
```
Programming Languages: Python, JavaScript, Go, Java, Ruby
Frameworks: Django, Flask, FastAPI, React, Vue, Angular
Databases: MySQL, PostgreSQL, MongoDB, Redis, Cassandra
Cloud: AWS, GCP, Azure
```

**After (prioritized for TechCorp):**
```
Programming Languages: Python (6 years), JavaScript, Go
Frameworks & Tools: FastAPI, Flask, Django, React
Databases: PostgreSQL, Redis, MySQL, MongoDB
Cloud Platforms: AWS (EC2, ECS, RDS, S3, Lambda), Docker, Kubernetes
```

**Changes:**
- ✅ Python first (their primary language)
- ✅ FastAPI first (mentioned in job)
- ✅ PostgreSQL first (their database)
- ✅ AWS expanded with specific services
- ✅ Less relevant tools de-emphasized

#### Experience Highlights Reordering

**Before:**
```
- Led team of 3 developers
- Improved code quality through reviews
- Migrated from monolith to microservices
- Designed RESTful APIs
```

**After (reordered for relevance):**
```
- Architected microservices platform using Python/FastAPI serving 100k+ users,
  achieving 99.9% uptime and 60% reduction in API latency (directly relevant
  to TechCorp's scale and tech stack)
- Designed and implemented RESTful APIs consumed by React frontend, collaborating
  closely with product team (relevant to cross-functional work mentioned in job)
- Led migration from monolith to microservices on AWS ECS, implementing CI/CD
  pipeline (matches their AWS infrastructure focus)
- Mentored 2 junior developers, establishing code review practices (aligns with
  TechCorp's value of continuous learning)
```

**Personalization:**
- ✅ Most relevant bullet first
- ✅ Added context linking to company needs
- ✅ Quantified results
- ✅ Mentioned matching technologies
- ✅ Connected to company values

### Phase 4: Save & Track (5% of time)

Three files created per job:

```
applications/12345_TechCorp_Solutions_Inc/
├── cv.md                      # Personalized CV (HTML comments removed)
├── cover_letter.md            # Personalized cover letter (clean)
└── company_research.json      # Full research findings
```

Tracker updated:
```json
{
  "job_id": "12345",
  "company": "TechCorp Solutions Inc.",
  "title": "Senior Backend Developer",
  "status": "completed",
  "directory": "applications/12345_TechCorp_Solutions_Inc",
  "created_at": "2025-11-22T15:30:00Z",
  "research_quality": "high",
  "files_created": ["cv.md", "cover_letter.md", "company_research.json"],
  "processing_time_seconds": 287
}
```

## Research Quality Levels

### High Quality
- Company website fully accessible
- Mission, values, products clearly identified
- Tech stack discovered (via blog/careers)
- 3+ recent news items found (last 6 months)
- Cultural insights available
- 6+ personalization hooks

### Medium Quality
- Basic company info available
- Some products/services identified
- Partial tech stack info
- 1-2 news items
- 3-4 personalization hooks

### Low Quality
- Minimal company info (website down/basic)
- Generic industry information only
- No recent news
- 1-2 personalization hooks
- Rely mainly on job posting data

**Note:** Agent creates best possible documents even with low-quality research.

## Processing Flow

### Sequential Processing (One Job at a Time)

```
Job 1: TechCorp Solutions Inc.
  ↓
  1. Fresh agent spawns
  2. Research TechCorp (website, search, analyze job)
  3. Personalize cover letter (6 sections)
  4. Personalize CV (5 sections)
  5. Save 3 files
  6. Update tracker
  7. Report: ✅ [1/47] TechCorp - Senior Backend Developer
  ↓
Job 2: Digital Innovations LLC
  ↓
  1. Fresh agent spawns (new context)
  2. Research Digital Innovations
  3. Personalize documents
  4. Save files
  5. Update tracker
  6. Report: ✅ [2/47] Digital Innovations - Frontend Engineer
  ↓
[Continue for all jobs...]
  ↓
Completion Summary
```

**Critical:** Each job gets fresh research (no memory of previous jobs).

## Error Handling

### Company Website Inaccessible

If website is down (404, 403, timeout):
- ✅ Fall back to web search
- ✅ Use job posting information
- ✅ Mark research quality as "low"
- ✅ Still create documents (best effort)
- ❌ Do NOT fail entirely

### Minimal Information Found

If very little company info available:
- ✅ Focus on job requirements
- ✅ Use industry-standard language
- ✅ Emphasize technical fit over cultural fit
- ✅ Note limitations in research report
- ✅ Continue to next job

### Template Errors

If templates cannot be read:
- ❌ This is CRITICAL error
- ❌ Stop processing
- ❌ Report to user immediately

### Failed Jobs

Track failed jobs separately:
```json
{
  "job_id": "99999",
  "company": "StartupXYZ",
  "status": "failed",
  "error": "Company website not accessible",
  "attempted_at": "2025-11-22T15:45:00Z",
  "retry_possible": true
}
```

User can retry failed jobs later.

## Progress Reporting

### Every 5 Jobs
```
📊 Progress Update
==================
Completed: 15/47 (32%)
Successful: 14
Failed: 1

Recent:
  ✅ TechCorp Solutions Inc. - Senior Backend Developer
  ✅ Digital Innovations LLC - Frontend Engineer
  ✅ CloudScale Technologies - DevOps Engineer
  ✅ DataFlow Systems - Data Analyst
  ❌ StartupXYZ - Product Manager (website inaccessible)

ETA: 4 hours 12 minutes
```

### Final Summary
```
✅ Personalization Complete
===========================
Session: personalize_20251122_150000
Duration: 6 hours 23 minutes

Results:
  Total Jobs: 47
  Successful: 44 applications (94%)
  Failed: 3 jobs (6%)

Applications Created:
  ✓ 44 personalized CVs
  ✓ 44 personalized cover letters
  ✓ 44 company research reports

Average Quality:
  High: 35 applications (80%)
  Medium: 7 applications (16%)
  Low: 2 applications (4%)

Failed Jobs:
  1. StartupXYZ - Company website not accessible
  2. SecretCorp - No company information found
  3. PrivateFirm - Website requires login

Output: applications/[job_id]_[company_name]/
Tracker: output/database/applications_tracker.json
```

## Output Files

### Personalized CV (`cv.md`)

- All EDITABLE sections customized
- HTML comment markers removed
- Professional formatting maintained
- No [placeholder] text
- Company-specific tailoring

### Personalized Cover Letter (`cover_letter.md`)

- All EDITABLE sections customized
- Hiring manager name (if found)
- Company-specific references
- Recent news mentioned
- Genuine interest demonstrated
- Professional business letter format

### Company Research (`company_research.json`)

- Complete research findings
- Personalization hooks used
- Research quality assessment
- Tech stack identified
- Cultural insights
- Recent news items

### Application Tracker (`applications_tracker.json`)

- Session metadata
- All applications list
- Success/failure status
- Processing statistics
- Failed jobs with retry info

## Best Practices

### 1. Review Templates First

Before running `/personalize`:
- ✅ Ensure CV template has all your info
- ✅ Check cover letter template reads well
- ✅ Verify EDITABLE sections are marked correctly
- ✅ Test with one job first (filter for 1-2 jobs)

### 2. Quality Over Speed

- Agent spends 60% time on research (worth it)
- 5-10 minutes per job is normal
- Quality research = better personalization
- Don't rush the process

### 3. Review Output

After personalization:
- ✅ Read a few generated documents
- ✅ Check if personalization makes sense
- ✅ Verify company names are correct
- ✅ Ensure no [placeholder] text remains

### 4. Handle Failed Jobs

If jobs fail:
- Check error reason in tracker
- Retry manually if needed
- Some companies don't have public websites (okay)

### 5. Update Templates

If output isn't great:
- Improve your template content
- Add better EDITABLE section instructions
- Run personalization again (it's deterministic)

## Time Estimates

**Per Job:**
- Research: 3-5 minutes (60%)
- Cover Letter: 1-2 minutes (25%)
- CV: 30-60 seconds (10%)
- Save & Track: 20-30 seconds (5%)
- **Total: 5-8 minutes per job**

**For 47 Jobs:**
- Best case: 4 hours (5 min/job)
- Average: 6 hours (7.5 min/job)
- Worst case: 8 hours (10 min/job)

**You can walk away** - system runs autonomously

## Security & Safety

### What the System CAN Do
- ✅ Read CV and cover letter templates
- ✅ Fetch public company websites
- ✅ Search for company information
- ✅ Write to `applications/` directory
- ✅ Update tracking database
- ✅ Create markdown and JSON files

### What the System CANNOT Do
- ❌ Modify your template files
- ❌ Create executable scripts (.py, .sh, .js)
- ❌ Batch process multiple jobs at once
- ❌ Access personal data beyond templates
- ❌ Make up company information (research only)
- ❌ Write outside `applications/` directory

### Process Guarantees
- One job at a time (sequential)
- Fresh agent context per job
- No batching or shortcuts
- Deterministic process
- Full error recovery
- Complete audit trail

## Example Application

### Before (Generic)
```
Dear Hiring Manager,

I am interested in the Backend Developer position. I have experience with
backend development and am looking for new opportunities.

Sincerely,
John Doe
```

### After (Personalized for TechCorp)
```
Dear Sarah Johnson, Engineering Manager,

I am writing to express my strong interest in the Senior Backend Developer
position at TechCorp Solutions Inc. I was particularly drawn to your mission
of revolutionizing enterprise communication through AI-powered tools, especially
after reading about your recent Series B funding announcement and the launch of
your innovative AI features in February 2025.

What particularly excites me about TechCorp is your commitment to building
scalable, AI-enhanced communication platforms that serve enterprise customers.
I am especially impressed by your engineering blog's discussion of microservices
architecture and your adoption of modern Python frameworks, which aligns perfectly
with my 6 years of experience building production-grade backend systems.

With deep expertise in Python, FastAPI, PostgreSQL, and AWS—the exact stack I
noticed TechCorp utilizes—I have delivered high-performance SaaS solutions
serving 100k+ users. At DataCorp, I architected a microservices platform that
reduced API latency by 60% while maintaining 99.9% uptime, directly applicable
to the scalability challenges your backend team is solving.

I am confident I can contribute to TechCorp's mission through my experience with
distributed systems, my passion for mentoring junior developers (aligning with
your value of continuous learning), and my track record of delivering customer-
centric technical solutions in fast-paced environments.

I would welcome the opportunity to discuss how my background in building scalable
AI-enhanced systems can support TechCorp's continued growth and innovation.

Thank you for considering my application.

Sincerely,
John Doe
```

**Personalization Highlights:**
- ✅ Hiring manager name found and used
- ✅ Specific mission referenced
- ✅ Recent news mentioned (Series B, AI features)
- ✅ Tech stack match highlighted
- ✅ Company values aligned
- ✅ Products/blog referenced
- ✅ Quantifiable achievements
- ✅ Cultural fit demonstrated

## Troubleshooting

### No Personalization Happening

**Check:**
- Are EDITABLE sections properly marked in templates?
- Did agent complete research phase?
- Check company_research.json for findings

### Generic Personalization

**Possible Causes:**
- Low research quality (website unavailable)
- Company has minimal online presence
- Job posting has limited info

**Solutions:**
- Check research_quality in company_research.json
- Manually enhance template for this company
- Accept that some companies have less info available

### Processing Stuck

**If a job takes >15 minutes:**
- May be researching deeply (complex website)
- May be encountering website issues
- Check progress updates

**You can:**
- Wait (system will continue)
- Check applications_tracker.json for status

### Wrong Information

**If personalization uses incorrect details:**
- Check company_research.json for research accuracy
- May have confused with similar company
- Report as quality issue

## Next Steps After Personalization

Once all applications are personalized:

1. **Review Applications**
   - Read through generated documents
   - Check for any errors or odd phrasing
   - Verify company names and details

2. **Export to PDF**
   - Convert markdown to PDF for submission
   - Use consistent formatting

3. **Track Applications**
   - Use applications_tracker.json as base
   - Add application dates, responses
   - Track interview status

4. **Submit Applications**
   - Follow each company's application process
   - Include personalized CV and cover letter
   - Reference research for interviews

## Support Files

- **Templates:** `user_docs/cv_template.md`, `user_docs/cover_letter_template.md`
- **Command:** `.claude/commands/personalize.md`
- **Skill:** `.claude/skills/application-personalizer/SKILL.md`
- **Tracker:** `scripts/init_tracker.py`
- **Main Docs:** `README.md`

---

**Ready to create outstanding, personalized applications!**
