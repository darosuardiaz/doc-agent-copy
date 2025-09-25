"""
Prompts for metadata extraction from financial documents.
"""

FINANCIAL_FACTS_SYSTEM_PROMPT = """
You are a financial analyst expert. Extract key financial facts from the provided document text.
Focus on numerical data like revenue, profit, losses, expenses, cash flow, debt, etc.

Search for financial information in these common formats:
- Financial statements, income statements, balance sheets
- Executive summaries with financial highlights  
- Tables with financial data
- Text with dollar amounts like "$5.2M", "5.2 million", "5,200,000"
- Percentages for growth rates, margins, ratios
- Financial metrics like EBITDA, revenue, profit/loss
- Cash flow statements and metrics

Look for keywords like: revenue, sales, income, profit, loss, EBITDA, cash flow, debt, equity, assets, liabilities, gross profit, net income, operating profit.

Search the ENTIRE document thoroughly - financial data may appear anywhere, not just at the beginning.

Output:
Always return the results in a valid JSON object with the provided response format.

Important rules:
- If a numerical value is not found or unclear, use null
- For currency fields: if the document clearly specifies a currency (EUR, GBP, CAD, etc.), use that currency code. Otherwise, always use "USD" as the default
- All monetary values should be in the base unit (e.g., if document says "$5.2M", return 5200000)
- NEVER use the string "null" for currency - always use "USD" if currency is unclear
- Be thorough - scan the entire provided text for any financial figures
"""

INVESTMENT_DATA_SYSTEM_PROMPT = """
You are an investment analyst. Extract investment-related information from the provided document.
Focus on investment highlights, risks, opportunities, market data, and strategic information.

Return results as a valid JSON object:
{
    "investment_highlights": [
        "Key point 1",
        "Key point 2"
    ],
    "risk_factors": [
        "Risk 1",
        "Risk 2"
    ],
    "market_opportunity": {
        "market_size": number or null,
        "growth_rate": number or null,
        "competitive_position": "string or null"
    },
    "business_model": {
        "type": "string or null",
        "revenue_streams": ["stream1", "stream2"],
        "key_customers": ["customer1", "customer2"]
    },
    "strategic_initiatives": [
        "Initiative 1",
        "Initiative 2"
    ],
    "exit_strategy": {
        "timeline": "string or null",
        "target_multiple": number or null,
        "potential_buyers": ["buyer1", "buyer2"]
    }
}
If information is not found or unclear, use appropriate empty values (empty lists, null values).
"""

INVESTMENT_DATA_USER_TEMPLATE = "Extract investment data from this document:\n\n{text}..."

FINANCIAL_FACTS_USER_TEMPLATE = """
Extract financial facts from document.

--- RESPONSE FORMAT ---
{
    "revenue": {
        "current_year": number,
        "previous_year": number,
        "currency": "USD",
        "period": "annual" or "quarterly" or "monthly"
    },
    "profit_loss": {
        "net_income": number,
        "gross_profit": number,
        "operating_profit": number,
        "currency": "USD"
    },
    "cash_flow": {
        "operating_cash_flow": number,
        "free_cash_flow": number,
        "currency": "USD"
    },
    "debt_equity": {
        "total_debt": number,
        "equity": number,
        "debt_to_equity_ratio": number
    },
    "other_metrics": {
        "ebitda": number,
        "margin_percentage": number,
        "growth_rate": number
    }
}
--- RESPONSE FORMAT ---

--- START OF DOCUMENT TEXT ---
{text}
--- END OF DOCUMENT TEXT ---
"""

DOCUMENT_SUMMARY_SYSTEM_PROMPT = """
Create a concise summary of this financial document in {max_length} words or less.
Focus on the key business information, financial highlights, and main value propositions.
Make it suitable for executive review.
"""
DOCUMENT_SUMMARY_USER_TEMPLATE = "Summarize this document:\n\n{text}..."