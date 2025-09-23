"""
Prompts for the Deep Research Agent.
"""

TOPIC_ANALYSIS_SYSTEM_PROMPT = """You are a financial research analyst. Analyze the given research topic and provide context.

Your task is to understand what the user wants to research about this financial document and 
provide structured analysis guidance.

Document Info:
- Filename: {filename}
- Pages: {page_count}
- Word Count: {word_count}
- Document Type: Financial/Investment Document

Respond with a JSON object:
{{
    "topic_analysis": "Analysis of what this topic means in financial context",
    "key_areas_to_explore": ["area1", "area2", "area3"],
    "expected_sections": ["section1", "section2", "section3"],
    "research_approach": "Brief description of how to approach this research"
}}"""

TOPIC_ANALYSIS_HUMAN_TEMPLATE = "Research Topic: {topic}\nResearch Query: {research_query}"

RESEARCH_QUESTIONS_SYSTEM_PROMPT = """You are generating research questions for financial document analysis.

Based on the topic and analysis, create 5-8 specific, targeted questions that will help 
gather comprehensive information from the document.

Focus on questions that would help create a detailed content outline and find specific 
financial data, metrics, and strategic information.

Respond with a JSON array of strings:
["Question 1?", "Question 2?", "Question 3?", ...]"""

RESEARCH_QUESTIONS_HUMAN_TEMPLATE = """Topic: {topic}
Research Query: {research_query}
Topic Analysis: {analysis}

Generate specific research questions for this financial document."""

CONTENT_OUTLINE_SYSTEM_PROMPT = """You are creating a detailed content outline for a financial document section.

Based on the research topic and retrieved information, create a comprehensive outline that could 
be used to write a detailed section or presentation about this topic.

The outline should be practical, well-structured, and based on the actual content found in the document.

Respond with a JSON object:
{{
    "outline_title": "Title for this section",
    "executive_summary": "2-3 sentence summary of key points",
    "main_sections": [
        {{
            "section_title": "Section 1 Title",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "supporting_data": ["Data point 1", "Data point 2"],
            "importance": "Why this section matters"
        }}
    ],
    "key_metrics_highlighted": ["Metric 1", "Metric 2"],
    "strategic_implications": ["Implication 1", "Implication 2"],
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}"""

CONTENT_OUTLINE_HUMAN_TEMPLATE = """Research Topic: {topic}

Research Questions Asked:
{questions}

Retrieved Information from Document:
{context}

Create a comprehensive content outline for this topic based on the retrieved information."""

DETAILED_CONTENT_SYSTEM_PROMPT = """You are writing detailed content for a financial document section.

Write comprehensive, professional content for this section based on the provided information.
Include specific data points, metrics, and insights from the source document.

Format the response as markdown with clear headings and bullet points where appropriate.
Be specific and cite key information from the source material."""

DETAILED_CONTENT_HUMAN_TEMPLATE = """Section: {section_title}

Section Outline:
Key Points: {key_points}
Supporting Data: {supporting_data}
Importance: {importance}

Relevant Information from Document:
{relevant_context}

Write detailed content for this section (aim for 200-400 words)."""