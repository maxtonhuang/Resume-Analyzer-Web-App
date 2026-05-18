"""
prompts.py — all 8 system prompts used by analyzer.py.

Task 3 of the Day 4 lab (Track A).
Study material references:
  §3.3 Schema-First Prompt Design
  §6.1 Extraction Prompts
  §6.2 Evaluation Prompts
  §6.3 Feedback-Only Principle

Every prompt must follow ICCO structure:
  Instruction  — what the model must do
  Context      — relevant background (rubric tables, schema description)
  Constraints  — rules the model must not break
  Output       — the exact JSON schema expected

Every prompt (except OVERALL_SUMMARY_PROMPT) must end with:
  "Output ONLY a valid JSON object matching the schema above. No prose. No
  markdown fences. No commentary. Never rewrite or generate résumé content."

Temperature guidance (set in the ask_json() call in analyzer.py):
  Extraction prompts (RESUME_PROFILE, JD_PROFILE): 0.0
  Evaluation prompts (KEYWORD_MATCH, BULLET_QUALITY, JARGON, STRUCTURE, DEGREE): 0.2–0.3
  OVERALL_SUMMARY_PROMPT: 0.3
"""


# ---------------------------------------------------------------------------
# Extraction prompts
# ---------------------------------------------------------------------------

# Purpose: extract a structured candidate profile from plain résumé text.
# Input to ask_json(): system=RESUME_PROFILE_PROMPT, user="RÉSUMÉ TEXT:\n\n{text}"
# Expected output schema — all fields required; arrays may be empty:
# {
#   "name": "string",
#   "contact": {
#     "email": "string", "phone": "string", "linkedin": "string",
#     "github": "string", "portfolio": "string"
#   },
#   "summary": "string",
#   "education": [{"school": "string", "degree": "string",
#                  "graduation_date": "string", "courses": ["string"]}],
#   "projects":  [{"title": "string", "date": "string", "bullets": ["string"]}],
#   "experience":[{"title": "string", "company": "string",
#                  "date": "string", "bullets": ["string"]}],
#   "skills": {
#     "languages": ["string"], "frameworks": ["string"], "tools": ["string"],
#     "concepts": ["string"], "platforms": ["string"]
#   }
# }
RESUME_PROFILE_PROMPT = """
# [Instruction]
You are a resume parser. Extract a structured candidate profile from the plain-text resume provided in the user message. Populate every field of the JSON schema below using only information explicitly present in the resume.

# [Context]
The user message contains text extracted from a PDF resume. The text may contain extraction artifacts: irregular whitespace, broken lines from multi-column layouts, and unconventional section labels. Section names vary by candidate (e.g. "Experience" vs "Work Experience"). Some resumes omit common sections entirely.

# [Constraints]
- Copy text verbatim. Do not paraphrase, summarize, rewrite, translate, or generate any content.
- Do not invent, infer, or guess content that is not explicitly in the source text.
- For missing string fields, return "". For missing array fields, return [].
- Every field in the schema must be present in your output, even if empty.
- Preserve the exact spelling, casing, and punctuation of names, titles, companies, schools, and technologies.
- For "education", "projects", and "experience", each entry is a separate object in the array. Copy each bullet point verbatim as a separate string in the "bullets" array.
- Categorize each item in "skills" into exactly one bucket:
  - languages: programming languages (Python, C++, Java, JavaScript)
  - frameworks: libraries and frameworks (React, Django, Unity, Unreal Engine)
  - tools: development tools and software (Git, Docker, VS Code, Figma)
  - concepts: methodologies and abstract topics (OOP, Agile, REST APIs, Machine Learning)
  - platforms: operating systems and cloud platforms (Linux, AWS, iOS)

# [Output Schema]
{
  "name": "string",
  "contact": {
    "email": "string",
    "phone": "string",
    "linkedin": "string",
    "github": "string",
    "portfolio": "string"
  },
  "summary": "string",
  "education": [
    {
      "school": "string",
      "degree": "string",
      "graduation_date": "string",
      "courses": ["string"]
    }
  ],
  "projects": [
    {
      "title": "string",
      "date": "string",
      "bullets": ["string"]
    }
  ],
  "experience": [
    {
      "title": "string",
      "company": "string",
      "date": "string",
      "bullets": ["string"]
    }
  ],
  "skills": {
    "languages": ["string"],
    "frameworks": ["string"],
    "tools": ["string"],
    "concepts": ["string"],
    "platforms": ["string"]
  }
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: extract a structured JD profile from free-form job posting text.
# Input to ask_json(): system=JD_PROFILE_PROMPT, user="JOB DESCRIPTION TEXT:\n\n{text}"
# Expected output schema — all fields required; arrays may be empty:
# {
#   "job_title": "string",
#   "company": "string",
#   "location": "string",
#   "experience_level": "string",
#   "required_skills": ["string"],
#   "preferred_skills": ["string"],
#   "tools_technologies": ["string"],
#   "responsibilities": ["string"],
#   "soft_skills": ["string"],
#   "buzzwords": ["string"],
#   "deal_breakers": ["string"]
# }
JD_PROFILE_PROMPT = """
# [Instruction]
You are a job description parser. Extract a structured job description profile from the free-form job posting text provided in the user message. Populate every field of the JSON schema below using only information explicitly present in the posting.

# [Context]
The user message contains free-form text from a job posting. Postings vary widely: some use clear headings like "Requirements" and "Responsibilities", others use prose paragraphs, and many mix the two. Required vs preferred skills may be distinguished by language ("must have" vs "nice to have") or by separate sections. Tools, technologies, and concepts are often mentioned in passing throughout the text rather than in a dedicated list.

# [Constraints]
- Copy text from the posting where possible. For list items (skills, responsibilities), preserve the exact wording rather than paraphrasing.
- Do not invent, infer, or guess content that is not in the source text.
- For missing string fields, return "". For missing array fields, return [].
- Every field in the schema must be present in your output, even if empty.
- "required_skills" includes skills explicitly framed as required, must-have, essential, or minimum qualifications.
- "preferred_skills" includes skills framed as nice-to-have, preferred, bonus, or a plus. If the posting does not distinguish required from preferred, treat everything as required_skills and leave preferred_skills empty.
- "tools_technologies" lists all specific named technical tools, languages, frameworks, libraries, and platforms mentioned anywhere in the posting. An item may also appear in required_skills or preferred_skills if it was framed that way; tools_technologies is a catalog of every named technology regardless of how it was framed.
- "responsibilities" lists day-to-day duties, deliverables, and ownership areas described in the posting.
- "soft_skills" includes non-technical traits and behaviors (communication, leadership, attention to detail, ownership).
- "buzzwords" includes vague culture or marketing language that signals fit rather than concrete requirements (e.g. "rockstar", "ninja", "passionate", "fast-paced environment", "wear many hats").
- "deal_breakers" includes hard exclusions or non-negotiables ("must be eligible to work in...", "no remote", "no exceptions"). Leave empty if none are stated.
- "experience_level" is a short string copied or summarized from the posting (e.g. "Entry-level", "Senior", "3-5 years", "Internship"). Leave empty if not stated.

# [Output Schema]
{
  "job_title": "string",
  "company": "string",
  "location": "string",
  "experience_level": "string",
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "tools_technologies": ["string"],
  "responsibilities": ["string"],
  "soft_skills": ["string"],
  "buzzwords": ["string"],
  "deal_breakers": ["string"]
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# ---------------------------------------------------------------------------
# Evaluation prompts
# ---------------------------------------------------------------------------

# Purpose: compare résumé keywords against JD requirements; produce a score.
# Input to ask_json():
#   system=KEYWORD_MATCH_PROMPT
#   user="RÉSUMÉ PROFILE:\n{json}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "present": [{"keyword": "string", "category": "language|framework|tool|concept|soft_skill|buzzword",
#                "found_in": "summary|projects|experience|education|skills", "exact_match": true}],
#   "missing": [{"keyword": "string", "category": "...", "importance": "required|preferred",
#                "suggested_section": "skills|projects|experience|summary",
#                "why_it_matters": "string (25 words max — diagnostic only)"}],
#   "keyword_match_score": 0
# }
# Scoring formula: 100 × (required_skills found in résumé) / max(1, total required_skills)
KEYWORD_MATCH_PROMPT = """
# [Instruction]
You are a resume-to-JD keyword matcher. Compare the candidate's resume profile against the job description profile. Identify which JD keywords are present in the resume and which are missing, then compute a keyword match score.

# [Context]
The user message contains two structured JSON profiles:
- RESUME PROFILE: extracted candidate data (skills, projects, experience, education, summary).
- JD PROFILE: extracted job description data (required_skills, preferred_skills, tools_technologies, soft_skills, buzzwords).

A keyword is any specific term from the JD that signals a hard or soft requirement: programming languages (Python), tools (Docker), frameworks (React), concepts (REST APIs), soft skills (communication), or buzzwords (rockstar).

# [Constraints]
- Diagnose only. Do not rewrite, suggest rewordings, or generate replacement content. The "why_it_matters" field describes why the gap matters, not how to fix it.
- A keyword is "present" only if it appears in the resume profile, in any field, with the same surface form or a clear case-insensitive equivalent (Python = python, AWS = aws). Treat trivial morphology as equivalent (API matches APIs). Set "exact_match" to true for identical spelling, false for case or morphology variants.
- "found_in" is the resume section where the keyword first appears: summary, projects, experience, education, or skills.
- "category" classifies the keyword as language, framework, tool, concept, soft_skill, or buzzword. Use the JD's framing to decide.
- "missing" includes every JD keyword not found in the resume. Set "importance" to "required" if the keyword comes from jd_profile.required_skills or jd_profile.tools_technologies (when the tool is framed as required), or "preferred" if from jd_profile.preferred_skills.
- "suggested_section" is the resume section where the missing keyword could most plausibly belong (skills, projects, experience, summary). This is a structural hint, not a rewrite.
- "why_it_matters" is at most 25 words, diagnostic only. Explain why the gap is significant for this role. Do not propose wording or rewrites.
- Source keywords from required_skills, preferred_skills, tools_technologies, soft_skills, and buzzwords in the JD profile. Do not invent keywords that are not in the JD profile.

# [Scoring]
total_required = number of items in jd_profile.required_skills.
required_found = number of items from jd_profile.required_skills that also appear in the "present" list (case and morphology equivalence allowed).
keyword_match_score = round(100 * required_found / max(1, total_required)).

Compute the count step by step before writing the JSON to avoid arithmetic errors.

# [Output Schema]
{
  "present": [
    {
      "keyword": "string",
      "category": "language|framework|tool|concept|soft_skill|buzzword",
      "found_in": "summary|projects|experience|education|skills",
      "exact_match": true
    }
  ],
  "missing": [
    {
      "keyword": "string",
      "category": "language|framework|tool|concept|soft_skill|buzzword",
      "importance": "required|preferred",
      "suggested_section": "skills|projects|experience|summary",
      "why_it_matters": "string"
    }
  ],
  "keyword_match_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: score each résumé bullet against the Action → Technology → Impact rubric.
# Input to ask_json(): system=BULLET_QUALITY_PROMPT, user="RÉSUMÉ PROFILE:\n{json}"
# Expected output schema:
# {
#   "bullets": [{"source": "projects|experience", "parent_title": "string",
#                "bullet_text": "string (verbatim)", "has_action_verb": true,
#                "has_specific_technology": true, "has_measurable_impact": false,
#                "level": "L1_OK|L2_BETTER|L3_BEST",
#                "what_is_missing": "string (20 words max — diagnose only)"}],
#   "bullet_quality_avg": 0
# }
# Scoring formula: round(100 × sum(level_score) / (3 × count)) where L1=1, L2=2, L3=3
# IMPORTANT: embed the Action→Technology→Impact rubric verbatim inside this prompt,
# including the L1/L2/L3 reference level examples.
BULLET_QUALITY_PROMPT = """
# [Instruction]
You are a resume bullet quality evaluator. Score each bullet point in the candidate's projects and experience against the Action / Technology / Impact (ATI) rubric. For every bullet, decide whether each ATI element is present, assign a level, and identify what is missing. Then compute the bullet quality average.

# [Context]
The user message contains the candidate's RESUME PROFILE as JSON. The "bullets" array of every entry in projects[] and experience[] contains the strings to evaluate. Each bullet is one resume line and is evaluated independently.

# [ATI Rubric (verbatim)]

Every bullet point follows the same three-part formula.

ACTION
  Strong past-tense verb.
  Examples: Developed, Optimised, Implemented, Led, Designed.

TECHNOLOGY
  Named tool, language, or framework.
  Examples: in C++, using Unity, with REST API, via AWS.

IMPACT
  Quantified outcome.
  Examples: reducing crashes by 70%, deployed to 500 players.

Weak bullet (no ATI structure):
  "Worked on a game project with a team and fixed bugs."

Full ATI bullet (all three elements):
  "Optimised collision detection in C++ reducing frame drops by 40% across all platforms."

# [Level Definitions]
- L3_BEST: all three ATI elements present (action verb AND named technology AND quantified impact).
- L2_BETTER: exactly two of the three elements present.
- L1_OK: zero or one element present.

# [Constraints]
- Iterate over every bullet in every projects[].bullets and experience[].bullets array. Do not skip any bullet.
- "bullet_text" must be the bullet copied verbatim. Do not paraphrase or clean up wording.
- "parent_title" is the project title for project bullets, or the role title plus company for experience bullets (e.g. "Software Intern at Acme").
- "source" is "projects" or "experience" depending on where the bullet came from.
- has_action_verb is true only when the bullet starts with or clearly contains a strong past-tense action verb in the spirit of the rubric examples. Generic verbs such as "worked", "helped", "did", "was involved in" do not qualify.
- has_specific_technology is true only when at least one named tool, language, framework, or platform is mentioned. Generic phrases such as "various tools" or "modern technologies" do not qualify.
- has_measurable_impact is true only when there is a quantified outcome: a number, a percentage, a count, a scale, a benchmark. Vague phrases such as "improved performance" or "many users" do not qualify.
- Assign "level" strictly by counting the three boolean flags: three true flags = L3_BEST, two = L2_BETTER, zero or one = L1_OK.
- "what_is_missing" is at most 20 words, diagnostic only. Name the missing ATI element(s) by category. Do not propose replacement wording, suggested verbs, suggested technologies, or suggested numbers. For L3_BEST bullets, return "".
- Diagnose only across the entire output. Do not generate sample rewrites or proposed bullet drafts anywhere.

# [Scoring]
For each bullet: level_score = 1 if L1_OK, 2 if L2_BETTER, 3 if L3_BEST.
count = total number of bullets evaluated.
bullet_quality_avg = round(100 * sum(level_score) / (3 * count)).
If count is 0, return 0.

# [Output Schema]
{
  "bullets": [
    {
      "source": "projects|experience",
      "parent_title": "string",
      "bullet_text": "string",
      "has_action_verb": true,
      "has_specific_technology": true,
      "has_measurable_impact": false,
      "level": "L1_OK|L2_BETTER|L3_BEST",
      "what_is_missing": "string"
    }
  ],
  "bullet_quality_avg": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: detect game-dev jargon that should be translated for non-game recruiters.
# Input to ask_json():
#   system=JARGON_AUDIT_PROMPT
#   user="DEGREE PROGRAM: {code}\n\nRÉSUMÉ PROFILE:\n{json}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "flags": [{"bullet_text": "string (verbatim)", "term_used": "string",
#              "suggested_translation": "string (from the table only)",
#              "severity": "low|medium|high"}],
#   "jargon_score": 0
# }
# Severity rules: high if JD has no game-dev language; medium if mixed; low if game studio role.
# Scoring formula: max(0, 100 - 10*high_count - 5*medium_count - 2*low_count)
# IMPORTANT: embed the full 15-row Game-Dev → SE translation table verbatim.
JARGON_AUDIT_PROMPT = """
# [Instruction]
You are a resume jargon auditor. Scan the candidate's resume bullets for game-development jargon that may confuse recruiters in non-game software roles. For each jargon term found, flag the bullet, identify the term used, propose the industry-standard translation from the embedded table only, and assign a severity level. Then compute the jargon score.

# [Context]
The user message contains the candidate's DEGREE PROGRAM code (one of RTIS, IMGD, UXGD, BFA), the RESUME PROFILE as JSON, and the JD PROFILE as JSON. The JD PROFILE indicates whether the target role uses game-dev language (game studio postings) or general software language. The JD's vocabulary determines the severity tier.

# [Jargon Translation Table (verbatim, 15 rows)]

| Game-Dev Term                    | Industry-Friendly Translation                                |
| -------------------------------- | ------------------------------------------------------------ |
| Game loop                        | Real-time application loop / event-driven architecture       |
| Sprite rendering                 | 2D graphics rendering                                        |
| Level editor                     | Developer tooling / content authoring tool                   |
| Level scripting                  | Gameplay automation / scripting layer                        |
| Mob spawner / enemy AI           | Entity management system / behaviour system                  |
| HP bar / HUD                     | Real-time UI rendering / overlay system                      |
| Collision detection (SAT, AABB)  | Computational geometry / spatial algorithms                  |
| Gameplay programmer              | Application developer / systems programmer                   |
| Shipped a game                   | Delivered a software product to end users                    |
| Game jam (48 hours)              | Rapid prototyping under time constraints                     |
| Tiled map loading                | Data-driven level/content loading from structured files      |
| Component-based engine           | Component architecture / ECS (Entity-Component-System)       |
| Asset pipeline                   | Content/data pipeline / build automation                     |
| Frame rate optimisation          | Performance profiling and optimisation                       |
| Multiplayer netcode              | Real-time network programming / client-server architecture   |

# [Severity Rules]
Determine severity once for the entire analysis, based on the JD context. All flags in the output share this severity.
- low: the JD profile indicates a game studio or game-dev role. Signals: jd_profile.job_title contains "game", "gameplay", "engine", or names like Unity, Unreal; or required_skills explicitly include game development.
- medium: the JD profile mixes game and non-game language. Some game-related terms appear alongside general software terms.
- high: the JD profile contains no game-dev language at all. The role is general software, web, data, infrastructure, or similar.

# [Constraints]
- Diagnose only. Flag the term and propose the translation taken verbatim from the table. Do not draft any rewritten bullet text or propose how to insert the translation into the bullet.
- Only flag terms that appear in the table above. Do not invent new entries or extend the table.
- A flag is generated per bullet per detected term. The same bullet can produce multiple flags if it contains multiple table terms.
- "bullet_text" is the bullet copied verbatim from the resume profile.
- "term_used" is the surface phrase from the bullet that matches the table row (e.g. "HUD" if the bullet says "built a HUD"; "enemy AI" if the bullet says "implemented enemy AI").
- "suggested_translation" must be copied verbatim from the right-hand column of the corresponding row.
- "severity" is the same for every flag in this output, set per the SEVERITY RULES above.
- If the JD has no game-dev language and the resume has many flags, do not soften severity. The diagnostic exists to surface the gap.
- Scan only bullets in projects[].bullets and experience[].bullets. Do not flag terms in skills lists, section headings, or the summary.

# [Scoring]
high_count = number of flags with severity "high".
medium_count = number of flags with severity "medium".
low_count = number of flags with severity "low".
jargon_score = max(0, 100 - 10 * high_count - 5 * medium_count - 2 * low_count).

Compute the counts and the score step by step before writing the JSON.

# [Output Schema]
{
  "flags": [
    {
      "bullet_text": "string",
      "term_used": "string",
      "suggested_translation": "string",
      "severity": "low|medium|high"
    }
  ],
  "jargon_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: audit Three-Thirds layout compliance and ATS formatting.
# Input to ask_json(): system=STRUCTURE_AUDIT_PROMPT, user="RÉSUMÉ TEXT:\n\n{text}"
# Expected output schema:
# {
#   "page_count_estimate": 1,
#   "single_column_likely": true,
#   "section_headings_present": ["string"],
#   "section_headings_missing": ["string"],
#   "three_thirds": {
#     "top_third_has_name": true,
#     "top_third_has_contact": true,
#     "top_third_has_summary_or_featured": true,
#     "middle_third_has_projects_or_experience": true,
#     "bottom_third_has_skills_keywords": true
#   },
#   "ats_red_flags": [{"issue": "string", "evidence": "string"}],
#   "structure_score": 0
# }
# IMPORTANT: embed the Three-Thirds zone table and ATS formatting rules verbatim.
STRUCTURE_AUDIT_PROMPT = """
# [Instruction]
You are a resume structure and ATS formatting auditor. Audit the candidate's resume for layout compliance with the Three-Thirds structure and for common ATS formatting issues. Identify what is present, what is missing, and what could trip up an ATS parser. Compute a structure score.

# [Context]
The user message contains the raw plain-text resume produced by PDF text extraction. Visual layout is lost but reading order is largely preserved. Infer the original layout from textual cues: line position, blank-line clustering, section headings, character density, and unusual characters. Single-column text usually extracts as continuous lines; multi-column layouts often interleave content from different columns in jarring ways. Visual styling such as font family, font size, colour, and bold weight is not recoverable from extracted text; rules that depend on those signals are out of scope for this audit.

# [Three-Thirds Reference (verbatim)]

One page. Three zones. Different jobs.

TOP THIRD (Human Eyes)
  Prime real estate. 5-10 second scan.
  Contents: Name (14-18pt), contact, professional summary mirroring the JD language, and the single strongest project.

MIDDLE THIRD (Depth)
  2-3 projects or internships. Bold title plus dates. 1-3 ATI bullet points each.
  Contents: Specific named tools, technologies, and measurable outcomes.

BOTTOM THIRD (ATS Keywords)
  Every keyword from the JD goes here. Use 8-9pt font for density.
  Contents: Education, Technical Skills, Concepts, Areas of Interest.

# [ATS Formatting Rules (verbatim)]

Do's:
- Single-column: use a single-column layout, no side panels, no two-column designs.
- Standard fonts: Calibri or Arial, 10-11pt for body text. [Not detectable from extracted text.]
- Clear headings: use standard section headings in ALL CAPS or bold (e.g. EDUCATION, PROJECTS, SKILLS).
- Bullet points: use simple bullet points (the standard PDF bullet character, Unicode U+2022) for each achievement.
- PDF format: save as .pdf to preserve formatting across all devices. [Implicit in this pipeline.]
- Exactly one page: keep it to exactly one page, no more, no less.

Don'ts:
- No tables or multi-column layouts: ATS cannot parse them reliably.
- No important text in page headers or footers: some ATS ignores these areas entirely.
- No text boxes or shapes: their content is often skipped by parsers.
- No profile photo: not expected in Singapore tech roles and wastes space.
- No icons or skill-level rating bars (e.g. star ratings next to a skill, Unicode U+2605 filled star and U+2606 outlined star are typical glyphs): ATS cannot read images or interpret rating glyphs.
- No colour for essential information: ATS reads plain text only. [Not detectable from extracted text.]

# [Detection Guidance]
You receive plain extracted text. Some rules can be checked from text and some cannot.

Detectable from extracted text:
- page_count_estimate: estimate from character count.
- single_column_likely: from text interleaving patterns.
- Section headings in ALL CAPS: case is preserved through extraction.
- Standard heading names: match against the expected vocabulary.
- Bullet point character used: look for the U+2022 bullet character at the start of item lines, or substitutes such as hyphen-minus, asterisk, or no bullet at all.
- Skill-level rating bars: look for repeated star characters (U+2605, U+2606, U+2730 or similar), repeated dot or circle characters used as filled-vs-empty ratings, or numeric rating patterns such as "4/5", "8/10", or percentages next to a skill name.
- Profile photo: indirect signal only. Look for image references the extractor preserves, or a suspiciously sparse top section before the first heading.
- Tables: detect from regular column spacing or tab-separated rows.
- Headers/footers: detect from short lines repeating across implicit page boundaries (page numbers, names).

Not detectable from extracted text (do not flag these):
- Font family (Calibri vs other).
- Font size in points.
- Colour usage.
- Bold weight when not paired with ALL CAPS.

# [Standard Section Headings To Expect]
Summary, Education, Experience (or Work Experience), Projects, Skills (or Technical Skills).

# [Constraints]
- Diagnose only. Do not propose rewrites, alternative phrasings, or replacement content anywhere in the output.
- page_count_estimate is an integer based on text density. Roughly: under 4000 characters is 1 page; 4000 to 8000 is 2 pages; over 8000 is 3 or more pages.
- single_column_likely is true if the extracted text reads in coherent top-to-bottom order without jarring interleaving of unrelated lines, false if the text looks like two columns merged.
- section_headings_present lists standard section labels detected in the text. Use canonical names from the STANDARD SECTION HEADINGS TO EXPECT list when reporting (normalise "Work Experience" to "Experience", "Technical Skills" to "Skills"). Headings in ALL CAPS are an ATS positive and do not require a red flag; headings present but in non-standard or decorative form should produce an ats_red_flags entry.
- section_headings_missing lists standard headings from that list that are not present in the resume in any case form.
- three_thirds: evaluate each boolean by checking whether the corresponding content appears in the expected vertical region. Approximate the regions by splitting the resume text into thirds by character count.
- ats_red_flags: each entry has "issue" (short label such as "Multi-column layout", "Skill-level rating bars present", "Profile photo likely present", "Page count exceeds one", "Decorative section heading format") and "evidence" (a short verbatim snippet from the text demonstrating the issue, or a brief description of the textual symptom). Only flag issues with concrete textual evidence; do not speculate. Do not flag rules listed under "Not detectable from extracted text" above.

# [Scoring]
Start at 100.
- Subtract 10 for each three_thirds boolean that is false. Range of this deduction is 0 to -50.
- Subtract 15 if single_column_likely is false.
- Subtract 10 if page_count_estimate is greater than 1.
- Subtract 3 for each entry in section_headings_missing.
- Subtract 5 for each entry in ats_red_flags.
Clamp the final value to the range 0 to 100. Write the result to structure_score.

# [Output Schema]
{
  "page_count_estimate": 1,
  "single_column_likely": true,
  "section_headings_present": ["string"],
  "section_headings_missing": ["string"],
  "three_thirds": {
    "top_third_has_name": true,
    "top_third_has_contact": true,
    "top_third_has_summary_or_featured": true,
    "middle_third_has_projects_or_experience": true,
    "bottom_third_has_skills_keywords": true
  },
  "ats_red_flags": [
    {
      "issue": "string",
      "evidence": "string"
    }
  ],
  "structure_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# Purpose: assess how well the JD's job title fits the student's degree programme.
# Input to ask_json():
#   system=DEGREE_ALIGNMENT_PROMPT
#   user="DEGREE PROGRAM: {code}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "student_degree": "string",
#   "jd_title": "string",
#   "title_on_suggested_list": true,
#   "matched_against": "string (the suggested-titles list used)",
#   "fit_commentary": "string (2–3 sentences — diagnostic only)",
#   "degree_alignment_score": 0
# }
# Include in context: the four degree-code → suggested job title lists from
# reference/Personal_Resume_Handout.md.
DEGREE_ALIGNMENT_PROMPT = """
# [Instruction]
You are a degree-to-job-title alignment evaluator. Assess how well the job description's title fits the student's degree programme. Determine whether the title appears on the student's own list of recommended job titles, on a sibling degree's list, or on no list at all. Write a brief diagnostic fit commentary and assign a degree alignment score.

# [Context]
The user message contains the student's DEGREE PROGRAM code and the JD PROFILE as JSON. The DEGREE PROGRAM code is one of: RTIS, IMGD, UXGD, BFA. Each degree has a focus-area description and a list of recommended job titles. The lists overlap: titles such as "Systems Engineer" appear on multiple degree lists, reflecting genuine cross-degree career paths.

# [Degree Reference (verbatim, 4 programmes)]

RTIS (Real-Time Interactive Simulation)
  Focus Areas: Low latency systems, engine development, high-performance computing, systems programming.
  Suggested Titles: Game Engine Developer, Systems Engineer, Site Reliability Engineer (SRE), DevOps Engineer, AI/ML Engineer, Data Analyst / Data Scientist, Full Stack Developer, Cybersecurity Engineer, Simulation Engineer, Graphics Programmer, Technical Product Manager, Technical Project Manager.

IMGD (Interactive Media & Game Development)
  Focus Areas: Interactive systems, real-time rendering, game systems, immersive visualisation.
  Suggested Titles: Game Developer, Systems Engineer, Full Stack Developer, Data Engineer, Infrastructure Engineer, DevOps Engineer, Cybersecurity Engineer, AI/ML Engineer, Technical Designer, Technical Artist, Gameplay Programmer, Tools Engineer, Technical Product Manager, Technical Project Manager.

UXGD (User Experience & Game Design)
  Focus Areas: UX design, software engineering, product strategy, digital product management.
  Suggested Titles: App Developer, UI/UX Designer, Product Designer, Product Manager, Product Operations Manager, Project Manager, Marketing & Design Specialist, Process Architect, Technical Designer, Technical Artist, UX Researcher, UX Engineer.

BFA (Digital Art and Animation)
  Focus Areas: Visual storytelling, CG production, game engine projects.
  Suggested Titles: Technical Artist, UI/UX Designer, Creative Designer, Unreal Engine Artist, 3D Graphic Artist, Production Assistant, Project Manager, Project Operations.

# [Degree Proximity Map]
The four degrees sit along a technical-to-creative spectrum: RTIS, IMGD, UXGD, BFA.

Close sibling pairs (heavy overlap in skills and titles):
  RTIS and IMGD

Moderate sibling pairs (some overlap in interactive systems and design):
  IMGD and UXGD
  UXGD and BFA

Distant pairs (little overlap):
  RTIS and UXGD
  IMGD and BFA

Far pairs (almost no overlap):
  RTIS and BFA

# [Constraints]
- Diagnose only. The fit_commentary describes why the fit is strong, partial, or weak. Do not suggest different roles, do not propose rewrites, do not draft replacement content.
- student_degree: copy the degree code verbatim from the DEGREE PROGRAM input (e.g. "RTIS").
- jd_title: copy the job title verbatim from jd_profile.job_title.
- title_on_suggested_list: true only if the JD title appears on the student's own degree list, treating obvious case and punctuation variants as equivalent (e.g. "AI/ML Engineer" matches "ai/ml engineer"). "Software Engineer" does not match "Full Stack Developer". Where a list entry contains a slash separator (e.g. "Data Analyst / Data Scientist"), treat the entry as matching either side of the slash.
- matched_against: the name of the suggested-titles list used as the basis for the score. Format as the degree code followed by the phrase "suggested titles" (e.g. "RTIS suggested titles"). If no list contains the title, set to "none".
- fit_commentary: 2 to 3 sentences, diagnostic. State whether the title is a direct match, sibling match, distant match, or off-list, and briefly explain in terms of the student's degree focus areas. No rewrites, no role suggestions.

# [Scoring]
Use these anchors for degree_alignment_score, then refine if needed:

  100: JD title is on the student's own degree list (direct match).
  75:  JD title is on a close sibling degree's list (RTIS-IMGD pair).
  50:  JD title is on a moderate sibling degree's list (IMGD-UXGD pair, or UXGD-BFA pair).
  25:  JD title is on a distant or far degree's list (RTIS-UXGD, IMGD-BFA, or RTIS-BFA).
  10:  JD title is on no list but conceptually relates to the student's focus areas.
  0:   JD title bears no relationship to the student's focus areas.

Refinements (apply at most one, after picking the anchor):
- If the JD title is not a verbatim match but is a close paraphrase of a title on the relevant list (e.g. "Backend Engineer" for "Full Stack Developer"), subtract 10 to 15 points from the anchor.
- If the JD title is a verbatim match but the JD's required_skills lean heavily toward a different degree's focus areas, subtract up to 10 points.

Round the final score to the nearest integer.

# [Output Schema]
{
  "student_degree": "string",
  "jd_title": "string",
  "title_on_suggested_list": true,
  "matched_against": "string",
  "fit_commentary": "string",
  "degree_alignment_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
"""


# ---------------------------------------------------------------------------
# Synthesis prompt
# ---------------------------------------------------------------------------

# Purpose: produce a 3-bullet plain Markdown executive summary from the full report.
# Input to ask_text(): system=OVERALL_SUMMARY_PROMPT, user="ANALYSIS REPORT:\n{json}"
# Returns: plain Markdown string (not JSON).
# NOTE: this prompt does NOT need the JSON output constraint line.
#       It also does NOT need a JSON schema — ask_text() is used, not ask_json().
# The summary must be diagnostic only — no rewrites, no generated résumé content.
OVERALL_SUMMARY_PROMPT = """
# [Instruction]
You are a resume analysis executive summary writer. Generate a 3-bullet plain Markdown executive summary of the candidate's resume analysis report.

# [Context]
The user message contains the ANALYSIS REPORT as JSON. Expected fields:
- overall_score: integer 0-100, the weighted composite of the five sub-scores.
- passes_ats_threshold: boolean indicating whether the composite cleared the ATS pass threshold. The threshold value itself is not in the report; do not invent one.
- keyword_match: keyword presence and absence, plus keyword_match_score (40% of composite).
- bullets: per-bullet ATI scoring and bullet_quality_avg (25% of composite).
- structure: Three-Thirds compliance, ATS red flags, and structure_score (15% of composite).
- jargon: game-dev jargon flags and jargon_score (10% of composite).
- degree_alignment: JD title vs degree fit and degree_alignment_score (10% of composite).

The summary is the candidate-facing artifact. It is a triage tool: it tells the candidate where they stand and what to focus on, without doing the work for them. Many readers will not look past the three bullets.

# [Constraints]
- Diagnose only. Do not propose rewritten bullets, suggested wording, replacement content, or specific phrasing changes. Name strengths and gaps; do not draft fixes.
- Output exactly 3 bullets in plain Markdown. Each bullet starts with "- " (hyphen, space).
- Each bullet is 1 to 2 sentences. Be specific: name actual scores, counts, or items pulled from the report. Avoid generic praise or generic criticism.
- Use plain Markdown only. Inline **bold** is allowed for key numbers or labels. No headings, no nested lists, no code fences, no preamble, no closing line.
- Do not invent scores, counts, facts, or thresholds that are not in the report.
- If passes_ats_threshold is referenced, acknowledge that ATS thresholds are heuristics that vary by company, in a few words.

# [Content Guidance]
The three bullets together should cover the topics below. Treat these as things not to miss, not as fixed slot assignments; the model decides which topic goes in which bullet and may combine related topics.

- Overall standing: the composite overall_score and the passes_ats_threshold result. A short note that ATS thresholds vary by company fits naturally here.
- Highest-leverage gap: the dimension dragging the score down hardest, with a specific number or named item. Examples of what "specific" looks like: a count of missing required keywords from keyword_match.missing, the bullet_quality_avg with a count of L1_OK bullets, a named ats_red_flags entry, a count of jargon flags when the JD is non-game, or a degree-title mismatch with the matched_against value.
- One more observation worth surfacing: usually the next-largest gap, or a notable strength (a strong sub-score the candidate should not lose). Pick whichever gives the reader the most useful additional context.

A reader skimming the three bullets should walk away knowing where they stand, what hurts them most, and one more piece of context that orients next steps.

# [Output]
Output the three Markdown bullets and nothing else. No preamble. No closing remarks. No JSON. No code fences.
"""
