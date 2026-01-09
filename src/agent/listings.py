"""
Baton Market Listings Data

To add a new listing:
1. Scrape the page with Firecrawl
2. Call add_listing_from_firecrawl(firecrawl_json)
3. Restart the agent

Or manually add to LISTINGS dict below.
"""

from langchain_core.documents import Document

# =============================================================================
# RAW LISTINGS DATA
# Each listing is a dict that can come from Firecrawl or be added manually
# =============================================================================

LISTINGS = {
    "453e1744": {
        "id": "453e1744",
        "title": "Established Festival & Talent Booking Business",
        "location": "Santa Fe Springs, CA",
        "status": "For Sale",
        "asking_price": 25000000,
        "revenue": 40777068,
        "cash_flow": 7889668,
        "multiple": 3.17,
        "employees_ft": 4,
        "employees_pt": 30,
        "advisor": "Fahad Salman",
        "industry": "Entertainment / Concert Promotion",
        "description": """
Entertainment business combining concert promotion and licensed talent agency.
Second-generation owner. Produces multi-day festivals across U.S. and Mexico,
with expansion plans for Central America.

Revenue breakdown: 70% events, 30% talent management (20% commission).
Clients include Live Nation, AEG Presents, and national promoters.
Founder open to advisory role post-sale.
        """,
        "risks": [
            "Event volatility - single cancelled event impacts quarterly revenue",
            "Founder dependency - artist relationships may not fully transfer",
            "Competition from Live Nation/AEG for major artists",
            "Economic sensitivity - entertainment is discretionary spending"
        ],
        "growth": [
            "Scale production capacity",
            "Expand artist roster with competitive advances",
            "Central America market expansion"
        ],
        "comparables": "Entertainment venues sold at 1.4X-2.8X. Premium justified by scale and relationships."
    },
    
    "d46b4e3f": {
        "id": "d46b4e3f",
        "title": "Luxury General Contractor – Resort Region, Class A License",
        "location": "Pinedale, WY",
        "status": "For Sale",
        "asking_price": 16800000,
        "revenue": 11832040,
        "cash_flow": 3082594,
        "multiple": 5.45,
        "employees_ft": 5,
        "employees_pt": 3,
        "advisor": "Reid Kleinman",
        "industry": "Construction / General Contractor",
        "description": """
Class A contractor serving ultra-high-net-worth clients in elite Western U.S. resort market.
Projects average $3-4M, 15-17 month duration, 12-14 active at any time.

Referral-based business. Founded 2018, current ownership since 2021.
Systems: Procore, Dropbox, Trello. Owner involvement: 25-35 hrs/week.
AR: $1.68M. Real estate optionally available.
        """,
        "risks": [
            "Geographic concentration in single resort market",
            "Ultra-high-net-worth clients sensitive to economic conditions",
            "Subcontractor availability in remote Wyoming location",
            "Long project cycles create cash flow timing issues"
        ],
        "growth": [
            "Semi-absentee ownership potential",
            "Expand to adjacent resort markets"
        ],
        "comparables": "Similar contractors sold at 4-5X. Premium for client base quality."
    },
    
    "dd1ac28d": {
        "id": "dd1ac28d",
        "title": "Scalable SaaS HR & Wellness Platform with 85% User Engagement",
        "location": "Pensacola Beach, FL",
        "status": "For Sale",
        "asking_price": 9000000,
        "revenue": 3979655,
        "cash_flow": 2948890,
        "multiple": 3.05,
        "employees_ft": 30,
        "employees_pt": 0,
        "advisor": "Fahad Salman",
        "industry": "Software / SaaS",
        "description": """
Employee engagement and wellness platform for mid-to-large U.S. employers.
Features: payroll, benefits, communications, chronic care management, live coaching.

Metrics: 85% user engagement, clients up to 125,000 employees.
Compliance: SOC2, HIPAA, NCQA certified. 10+ years in market.
Recurring revenue model. Fully remote, relocatable.
        """,
        "risks": [
            "Competitive HR/wellness SaaS market (Workday, BambooHR)",
            "Long enterprise sales cycles",
            "30-person team creates significant payroll obligation",
            "Platform requires ongoing technical maintenance"
        ],
        "growth": [
            "No formal sales function - huge growth lever",
            "Strategic buyer with distribution network could scale rapidly"
        ],
        "comparables": "SaaS companies typically 3-5X ARR. Strong engagement metrics justify premium."
    },
    
    "8cf95905": {
        "id": "8cf95905",
        "title": "Specialized Pharma Market Research Firm with Global Client Base",
        "location": "Riverside, CT",
        "status": "For Sale",
        "asking_price": 7000000,
        "revenue": 3184152,
        "cash_flow": 1618145,
        "multiple": 4.33,
        "employees_ft": 4,
        "employees_pt": 1,
        "advisor": "Ani Thakur",
        "industry": "Consulting / Biotech",
        "description": """
Custom market research consultancy exclusively serving pharmaceutical sector.
Services: market potential, positioning, pipeline development, lifecycle management.

Metrics: 85%+ repeat business, 12+ MSAs, 25% CAGR since 2019.
Margins: 60% gross, 43% net. GDPR/SOC2 compliant. Fully remote.
Team: 6 professionals with 10-25 years experience each.
        """,
        "risks": [
            "Concentration in pharma sector",
            "Key person dependency on senior consultants",
            "Project-based revenue (though high repeat rate)"
        ],
        "growth": [
            "Underutilized existing client accounts",
            "Expand service offerings"
        ],
        "comparables": "Consulting firms typically 3-4X. Premium for margins and repeat rate."
    },
    
    "0f6d8f18": {
        "id": "0f6d8f18",
        "title": "Established Midwest Cabinet Wholesaler With Strong B2B Base",
        "location": "Des Plaines, IL",
        "status": "For Sale",
        "asking_price": 9500393,
        "revenue": 8510611,
        "cash_flow": 1866442,
        "multiple": 5.09,
        "employees_ft": 18,
        "employees_pt": 5,
        "advisor": "Serena Lee",
        "industry": "Wholesale / Manufacturing",
        "description": """
B2B cabinet supplier to contractors, builders, retailers. Founded 2016.
Products: assembled kitchen/bath cabinets, 12+ colors, multi-state distribution.

Metrics: 90%+ repeat orders, 10-15% YoY growth.
Team: experienced, 6+ year tenure, cross-trained.
Real estate optionally available.

Reason for Sale: Diverging partner interests. 6-month transition offered.
        """,
        "risks": [
            "Housing market sensitivity",
            "Import/tariff exposure on cabinet materials",
            "Regional concentration in Midwest"
        ],
        "growth": [
            "Digital sales channel",
            "New product lines",
            "Expanded geographic distribution"
        ],
        "comparables": "Cabinet manufacturers sold at 3.7-4.0X. Premium for customer retention."
    },
    
    "1e9ce105": {
        "id": "1e9ce105",
        "title": "Passive-Income Logistics Company w/ Owned Terminal & 130+ Trucks",
        "location": "Franklinville, NJ",
        "status": "Under Contract",
        "asking_price": 14500000,
        "revenue": 16367931,
        "cash_flow": 1559403,
        "multiple": 9.30,
        "employees_ft": 40,
        "employees_pt": 5,
        "advisor": "Reid Kleinman",
        "industry": "Logistics / Transportation",
        "description": """
Asset-backed logistics across 48 states. Owns 20,000 sq ft terminal.
130+ trucks under management, 4,000+ customers.

Revenue: 60% transport, 30% investor truck program (40%+ margins), 10% other.
Growth: $3.6M (2023) → $12M (2024) → $20M projected. AI-enabled operations.
Investor program: 95%+ retention. Minimal owner involvement.
        """,
        "risks": [
            "High multiple (9.3X) requires strong growth execution",
            "Fuel price volatility",
            "Driver shortage industry-wide",
            "DOT/FMCSA regulatory compliance"
        ],
        "growth": [
            "Warehouse/cold storage utilization",
            "Truck parking monetization (300 trailers)",
            "Franchise model to Chicago, Dallas, Atlanta"
        ],
        "comparables": "Trucking companies typically 3-5X. Premium for growth trajectory and owned assets."
    },
    
    "091784a5": {
        "id": "091784a5",
        "title": "Remote US Tax & Bookkeeping Firm",
        "location": "Undisclosed",
        "status": "Under Contract",
        "asking_price": 3700000,
        "revenue": 2229675,
        "cash_flow": 1457607,
        "multiple": 2.54,
        "employees_ft": 2,
        "employees_pt": 19,
        "advisor": "Fahad Salman",
        "industry": "Professional Services / Tax",
        "description": """
Specializes in non-U.S. founders navigating U.S. tax compliance.
Expert in forms 5471/5472 (niche most CPAs avoid).

Revenue: 80% tax prep, 20% bookkeeping. 2x Inc. 5000 honoree.
Fully remote, international team, 2 IRS-enrolled agents.
Owners not involved in prep work - ideal for absentee.

Note: Resolved personnel issue, stability restored.
        """,
        "risks": [
            "Past personnel issues (resolved but worth noting)",
            "Seasonal revenue concentration in tax season",
            "Regulatory changes in international tax law"
        ],
        "growth": [
            "Underserved market with low competition",
            "Reactivate dormant marketing channels",
            "Expand recurring bookkeeping services"
        ],
        "comparables": "Tax/accounting firms typically 1-2X. Premium for niche expertise."
    },
}

# =============================================================================
# ADVISOR MAPPING
# =============================================================================

ADVISORS = {
    "453e1744": {"name": "Fahad Salman", "calendar": "https://cal.com/baton-market/fahad-salman"},
    "dd1ac28d": {"name": "Fahad Salman", "calendar": "https://cal.com/baton-market/fahad-salman"},
    "091784a5": {"name": "Fahad Salman", "calendar": "https://cal.com/baton-market/fahad-salman"},
    "d46b4e3f": {"name": "Reid Kleinman", "calendar": "https://cal.com/baton-market/reid-kleinman"},
    "1e9ce105": {"name": "Reid Kleinman", "calendar": "https://cal.com/baton-market/reid-kleinman"},
    "8cf95905": {"name": "Ani Thakur", "calendar": "https://cal.com/baton-market/ani-thakur"},
    "0f6d8f18": {"name": "Serena Lee", "calendar": "https://cal.com/baton-market/serena-lee"},
}

# =============================================================================
# FUNCTIONS TO CONVERT TO DOCUMENTS
# =============================================================================

def listing_to_document(listing: dict) -> Document:
    """Convert a listing dict to a LangChain Document for the vector store."""
    
    # Format price nicely
    price = f"${listing['asking_price']:,}"
    revenue = f"${listing['revenue']:,}"
    cash_flow = f"${listing['cash_flow']:,}"
    
    # Build content string
    content = f"""
Listing: {listing['title']}
Location: {listing['location']} | ID: {listing['id']} | Status: {listing['status']}

Asking: {price} | Revenue: {revenue} | Cash Flow: {cash_flow} | Multiple: {listing['multiple']}X
Employees: {listing['employees_ft']} FT, {listing['employees_pt']} PT | Advisor: {listing['advisor']}
Industry: {listing['industry']}

{listing['description'].strip()}

Risks: {', '.join(listing['risks'])}

Growth Opportunities: {', '.join(listing['growth'])}

{listing.get('comparables', '')}
    """
    
    return Document(
        page_content=content.strip(),
        metadata={
            "listing_id": listing['id'],
            "price": listing['asking_price'],
            "type": listing['industry'],
            "status": listing['status']
        }
    )


def get_all_documents() -> list[Document]:
    """Get all listings as Documents for the vector store."""
    return [listing_to_document(listing) for listing in LISTINGS.values()]


def get_listing(listing_id: str) -> dict | None:
    """Get a listing by ID."""
    return LISTINGS.get(listing_id)


def get_advisor(listing_id: str) -> dict:
    """Get advisor info for a listing."""
    return ADVISORS.get(listing_id, {"name": "Baton Advisor", "calendar": "https://cal.com/baton-market"})


# =============================================================================
# FIRECRAWL INGESTION
# =============================================================================

def parse_firecrawl_json(firecrawl_data: dict) -> dict:
    """
    Parse Firecrawl JSON into our listing format.
    
    This extracts structured data from the markdown that Firecrawl returns.
    You may need to adjust the parsing based on Baton's page structure.
    """
    markdown = firecrawl_data.get("markdown", "")
    metadata = firecrawl_data.get("metadata", {})
    
    # Extract listing ID from URL
    url = metadata.get("url", "") or metadata.get("sourceURL", "")
    listing_id = url.split("/")[-1].split("?")[0] if url else None
    
    # Try to extract data from markdown
    # This is basic - you might want to make it smarter
    listing = {
        "id": listing_id,
        "title": "",
        "location": "",
        "status": "For Sale",
        "asking_price": 0,
        "revenue": 0,
        "cash_flow": 0,
        "multiple": 0,
        "employees_ft": 0,
        "employees_pt": 0,
        "advisor": "",
        "industry": "",
        "description": "",
        "risks": [],
        "growth": [],
        "comparables": "",
        "raw_markdown": markdown  # Keep the raw markdown for reference
    }
    
    # Extract title from metadata
    listing["title"] = metadata.get("title", "").replace(" on Baton Market", "")
    
    # Parse numbers from markdown
    import re
    
    # Price pattern: ## $XX,XXX,XXX or $XX,XXX,XXX
    price_match = re.search(r'\$[\d,]+(?:,\d{3})*', markdown)
    if price_match:
        listing["asking_price"] = int(price_match.group().replace("$", "").replace(",", ""))
    
    # Revenue pattern: usually after "Gross Revenue"
    revenue_match = re.search(r'Gross Revenue[^\d]*\$([\d,]+)', markdown)
    if revenue_match:
        listing["revenue"] = int(revenue_match.group(1).replace(",", ""))
    
    # Cash flow pattern
    cf_match = re.search(r'(?:Adj\.|Adjusted)\s*Cash Flow[^\d]*\$([\d,]+)', markdown)
    if cf_match:
        listing["cash_flow"] = int(cf_match.group(1).replace(",", ""))
    
    # Multiple pattern
    mult_match = re.search(r'([\d.]+)X', markdown)
    if mult_match:
        listing["multiple"] = float(mult_match.group(1))
    
    # Employees pattern
    emp_match = re.search(r'(\d+)\s*FT,\s*(\d+)\s*PT', markdown)
    if emp_match:
        listing["employees_ft"] = int(emp_match.group(1))
        listing["employees_pt"] = int(emp_match.group(2))
    
    # Extract description - text after "About this Business"
    desc_match = re.search(r'About this Business.*?Not a franchise\s*(.*?)(?:Show more|Share|##)', markdown, re.DOTALL)
    if desc_match:
        listing["description"] = desc_match.group(1).strip()
    
    # Try to find advisor name
    advisor_match = re.search(r'([A-Z]+\s+[A-Z]+)\s*\n\s*Baton M&A Advisor', markdown)
    if advisor_match:
        listing["advisor"] = advisor_match.group(1).title()
    
    return listing


def add_listing_from_firecrawl(firecrawl_data: dict) -> str:
    """
    Add a new listing from Firecrawl JSON data.
    
    Usage:
        import json
        firecrawl_json = json.loads(your_firecrawl_response)
        result = add_listing_from_firecrawl(firecrawl_json)
        print(result)
    """
    listing = parse_firecrawl_json(firecrawl_data)
    
    if not listing["id"]:
        return "Error: Could not extract listing ID from URL"
    
    # Add to LISTINGS dict
    LISTINGS[listing["id"]] = listing
    
    # Add advisor mapping (default to Fahad if unknown)
    if listing["id"] not in ADVISORS:
        ADVISORS[listing["id"]] = {
            "name": listing.get("advisor") or "Fahad Salman",
            "calendar": "https://cal.com/baton-market/fahad-salman"
        }
    
    return f"Added listing {listing['id']}: {listing['title']}"


# =============================================================================
# QUICK SUMMARY FUNCTIONS
# =============================================================================

def get_listings_summary() -> str:
    """Get a formatted summary of all listings."""
    for_sale = []
    under_contract = []
    
    for lid, listing in LISTINGS.items():
        line = f"• {listing['title'][:40]}... (${listing['asking_price']/1e6:.1f}M) - {listing['location']} - {listing['multiple']}X"
        if listing['status'] == "Under Contract":
            under_contract.append(line)
        else:
            for_sale.append(line)
    
    output = "AVAILABLE LISTINGS:\n\nFOR SALE:\n"
    output += "\n".join(for_sale)
    
    if under_contract:
        output += "\n\nUNDER CONTRACT:\n"
        output += "\n".join(under_contract)
    
    return output
