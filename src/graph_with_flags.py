"""
Baton Two-Agent System - WITH FEATURE FLAGS
Demonstrates production-ready feature flag integration for:
- A/B testing agent behavior
- Gradual rollout of new features
- Kill switches for problematic features
- Per-user targeting

Changes from original:
1. Import feature flag system
2. Agents check flags before executing behavior
3. Prompts adapt based on flag state
4. Added flag status tool for debugging
"""
import sys
import os
import logging
import json
import re
import requests

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("BatonAgent")

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from listings import (
    get_all_documents,
    get_listings_summary,
    LISTINGS,
    ADVISORS,
)

# 🚩 FEATURE FLAGS IMPORT
from feature_flags import is_enabled, get_variant, get_feature_flags_status

# =============================================================================
# SETUP
# =============================================================================

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(get_all_documents())

AIRTABLE_WEBHOOK = os.getenv("AIRTABLE_WEBHOOK_URL")

def send_to_airtable(data: dict) -> str:
    """Send data to Airtable webhook. Returns a string status for the agent."""
    logger.info(f"🚀 FIRING AIRTABLE for: {data.get('email', 'No Email')} / {data.get('phone', 'No Phone')}")
    try:
        clean_data = json.loads(json.dumps(data, default=str))
        response = requests.post(AIRTABLE_WEBHOOK, json=clean_data, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Airtable Success")
            return "Lead successfully sent to Airtable."
        else:
            logger.error(f"❌ Airtable Failed: {response.status_code} - {response.text[:200]}")
            return f"Failed to send lead. Status: {response.status_code}"

    except Exception as e:
        logger.error(f"❌ Airtable Error: {str(e)}")
        return f"System Error sending lead: {str(e)}"


# =============================================================================
# HELPER: SMART LOOKUP
# =============================================================================

def resolve_listing_id(input_str: str) -> str | None:
    """Finds the listing ID even if the agent passes a Name."""
    input_str = str(input_str).strip()

    # 1) direct ID
    if input_str in LISTINGS:
        return input_str

    # 2) fuzzy title match
    logger.info(f"⚠️ ID '{input_str}' not found directly. Searching titles...")
    for lid, data in LISTINGS.items():
        if input_str.lower() in data["title"].lower():
            logger.info(f"✅ Resolved '{input_str}' -> {lid}")
            return lid

    return None


def normalize_email(email: str) -> str:
    """Basic cleanup (handles * -> @ from masked input)."""
    if not email:
        return ""
    return str(email).replace("*", "@").strip()


def normalize_phone(phone: str) -> str:
    """Keep digits only; good enough for 'has phone' checks + Airtable payload."""
    if not phone:
        return ""
    digits = re.sub(r"\D+", "", str(phone))
    return digits


def has_valid_phone(phone: str) -> bool:
    """Very light validation: 7+ digits."""
    digits = normalize_phone(phone)
    return len(digits) >= 7


# =============================================================================
# STATE (Enhanced with user tracking for feature flags)
# =============================================================================

class State(TypedDict):
    messages: Annotated[list, add_messages]
    buyer_name: str
    buyer_email: str
    buyer_phone: str
    interested_listing: str
    lead_captured: bool
    user_id: str  # 🚩 NEW: For feature flag targeting
    interaction_count: int  # 🚩 NEW: Track conversation depth


# =============================================================================
# CONCIERGE TOOLS (Agent 1)
# =============================================================================

def search_listings(query: str, state: State | None = None) -> str:
    """Search listings by any criteria."""
    logger.info(f"🔎 SEARCHING: {query}")
    
    # 🚩 Feature flag: Include under-contract listings?
    user_id = state.get("user_id") if state else None
    include_sold = is_enabled("show_under_contract", user_id)
    
    results = vector_store.similarity_search(query, k=3)
    if not results:
        return "No matching listings found."
    
    # Filter out under-contract if flag disabled
    if not include_sold:
        results = [r for r in results if "under contract" not in r.page_content.lower()]
    
    return "\n\n---\n\n".join([str(doc.page_content).strip() for doc in results])


def list_all_listings(state: State | None = None) -> str:
    """Show summary of all available listings."""
    user_id = state.get("user_id") if state else None
    
    # 🚩 Feature flag: Show under-contract for social proof?
    if is_enabled("show_under_contract", user_id):
        return str(get_listings_summary())
    else:
        # Filter to only "For Sale"
        summary = get_listings_summary()
        lines = summary.split("\n")
        filtered = []
        skip_section = False
        for line in lines:
            if "UNDER CONTRACT:" in line:
                skip_section = True
            if skip_section:
                continue
            filtered.append(line)
        return "\n".join(filtered)


def get_listing_details(listing_id: str, state: State | None = None) -> str:
    """Get full details. Handles IDs OR Names."""
    logger.info(f"📄 DETAILS REQUESTED: {listing_id}")

    real_id = resolve_listing_id(listing_id)
    if not real_id:
        return f"Could not find a listing matching '{listing_id}'. Try searching by keyword or asking for the list of all listings."

    listing = LISTINGS[real_id]
    user_id = state.get("user_id") if state else None
    
    # 🚩 Feature flags: Control what information to show
    show_risks = is_enabled("show_risks_upfront", user_id)
    show_comps = is_enabled("show_comparables", user_id)
    
    details = f"""
**{listing['title']}** (ID: {real_id})
Asking: ${listing['asking_price']:,} | Cash Flow: ${listing['cash_flow']:,}
Multiple: {listing['multiple']}X

{listing['description']}
""".strip()
    
    if show_risks:
        details += f"\n\nRisks: {', '.join(listing['risks'])}"
    
    if show_comps and listing.get('comparables'):
        details += f"\n\n{listing['comparables']}"
    
    return details


def handoff_to_listing_agent(listing_id: str) -> str:
    """
    Transfer to Listing/Booking agent.
    Use this when user wants deeper details or indicates interest.
    """
    real_id = resolve_listing_id(listing_id) or listing_id
    logger.info(f"🔄 HANDOFF to Listing Agent: {real_id}")
    return f"HANDOFF_LISTING:{real_id}"


# =============================================================================
# LISTING/BOOKING TOOLS (Agent 2)
# =============================================================================

def get_advisor_calendar(listing_id: str) -> str:
    """Get the calendar link (cal.com)."""
    real_id = resolve_listing_id(listing_id) or listing_id
    advisor = ADVISORS.get(real_id, {"calendar": "https://cal.com/baton-market"})
    return f"Book here: {advisor['calendar']}"


def capture_contact_info(
    listing_id: str,
    buyer_name: str = "",
    buyer_email: str = "",
    buyer_phone: str = "",
    contact_preference: str = "",
    preferences: str = "",
    state: State | None = None,
) -> str:
    """
    Fire Airtable webhook when:
      - (name & email) OR (name & phone)  [default]
      - (name & email & phone)  [if require_both_contacts flag enabled]
    """
    buyer_email = normalize_email(buyer_email)
    buyer_phone_clean = normalize_phone(buyer_phone)

    real_id = resolve_listing_id(listing_id) or listing_id
    advisor_info = ADVISORS.get(real_id, {"name": "Baton Advisor"})
    advisor_name = advisor_info.get("name", "Baton Advisor")

    has_name = len(str(buyer_name).strip()) > 1
    has_email = "@" in str(buyer_email)
    has_phone = has_valid_phone(buyer_phone_clean)

    logger.info(
        f"📝 CAPTURE: Name='{buyer_name}' Email='{buyer_email}' Phone='{buyer_phone_clean}' Listing='{real_id}'"
    )

    # 🚩 Feature flag: Require both email AND phone?
    user_id = state.get("user_id") if state else None
    require_both = is_enabled("require_both_contacts", user_id)
    
    can_submit = False
    if require_both:
        can_submit = has_name and has_email and has_phone
    else:
        can_submit = has_name and (has_email or has_phone)
    
    # ✅ SEND when criteria met
    if can_submit:
        payload = {
            "name": str(buyer_name).strip(),
            "email": str(buyer_email).strip() if has_email else "",
            "phone": str(buyer_phone_clean).strip() if has_phone else "",
            "listing_id": str(real_id),
            "contact_preference": str(contact_preference).strip() if contact_preference else "pending",
            "preferences": str(preferences).strip() if preferences else "",
            "advisor": str(advisor_name),
            "status": "new_lead",
        }
        status_msg = send_to_airtable(payload)
        return f"{status_msg} Advisor {advisor_name} has been notified."

    # Otherwise, request missing fields
    missing = []
    if not has_name:
        missing.append("your name")
    
    if require_both:
        if not has_email:
            missing.append("your email")
        if not has_phone:
            missing.append("your phone number")
    else:
        if not (has_email or has_phone):
            missing.append("your email or phone number")

    return f"I've captured some info, but I still need {' and '.join(missing)} to submit this to the advisor."


# =============================================================================
# 🚩 NEW TOOL: Feature Flag Status (for debugging)
# =============================================================================

def show_feature_flags() -> str:
    """
    Display current feature flag status.
    Useful for debugging or showing what's enabled.
    """
    return get_feature_flags_status()


# =============================================================================
# AGENTS (Enhanced with dynamic prompts based on flags)
# =============================================================================

# Agent 1 tools: greet + browse + handoff + flags
concierge_tools = [
    search_listings, 
    list_all_listings, 
    get_listing_details, 
    handoff_to_listing_agent,
    show_feature_flags  # 🚩 NEW: Debug tool
]

# Agent 2 tools: deeper details + booking + lead capture + flags
listing_booking_tools = [
    get_listing_details, 
    get_advisor_calendar, 
    capture_contact_info,
    show_feature_flags  # 🚩 NEW: Debug tool
]

concierge_model = ChatOpenAI(model="gpt-4o").bind_tools(concierge_tools)
listing_booking_model = ChatOpenAI(model="gpt-4o").bind_tools(listing_booking_tools)


def build_concierge_prompt(state: State) -> str:
    """🚩 Build dynamic prompt based on feature flags"""
    user_id = state.get("user_id", "")
    
    # Get A/B test variant for tone
    tone = get_variant("agent_tone", user_id, default="professional")
    
    # Check behavior flags
    early_advisor = is_enabled("early_advisor_intro", user_id)
    aggressive = is_enabled("aggressive_capture", user_id)
    
    base_prompt = f"""You are Baton's M&A Concierge (Agent 1).

Tone: {tone.upper()}
{"- Be crisp and consultative" if tone == "professional" else ""}
{"- Be warm and conversational" if tone == "casual" else ""}
{"- Be expert but approachable" if tone == "consultative" else ""}

Your job:
- Greet the buyer warmly and quickly.
- You have access to listings and can search or show summaries.
"""

    if early_advisor:
        base_prompt += "- 🚩 FEATURE ENABLED: Offer advisor connection proactively after every response.\n"
    else:
        base_prompt += "- Mention advisor connection is available, but don't push it.\n"
    
    if aggressive:
        base_prompt += "- 🚩 FEATURE ENABLED: After showing listing details, immediately ask for their contact info to connect them with the advisor.\n"
    
    base_prompt += """
- If the buyer expresses interest in a specific listing or asks for deeper details, call `handoff_to_listing_agent`
  with the listing ID or name immediately.

Behavior:
- Keep answers concise.
- If uncertain which listing they mean, ask a short clarifying question OR use `search_listings`.
"""
    
    return base_prompt


def build_listing_booking_prompt(state: State) -> str:
    """🚩 Build dynamic prompt based on feature flags"""
    user_id = state.get("user_id", "")
    
    # Get A/B test variant
    tone = get_variant("agent_tone", user_id, default="professional")
    
    # Check lead capture requirements
    require_both = is_enabled("require_both_contacts", user_id)
    collect_budget = is_enabled("collect_budget_upfront", user_id)
    
    base_prompt = f"""You are Baton's Listing + Booking Agent (Agent 2).

Tone: {tone.upper()}

Your job:
- Provide deeper details on the listing (use `get_listing_details` if needed).
- Offer two CTAs:
  1) Book a call via cal.com (use `get_advisor_calendar`)
  2) Get connected to an advisor by capturing contact info (use `capture_contact_info`)

Lead capture rule:
"""
    
    if require_both:
        base_prompt += "- 🚩 FEATURE ENABLED: You MUST collect name, email, AND phone before submitting.\n"
    else:
        base_prompt += "- The moment you have (name & email) OR (name & phone), call `capture_contact_info`.\n"
    
    if collect_budget:
        base_prompt += "- 🚩 FEATURE ENABLED: Ask about budget range and timeline before sharing details.\n"
    
    base_prompt += """- If you have extra info (preferences, timeline, budget range), include it in `preferences`.

Tone:
- Crisp and helpful.
- Don't overtalk. Move the user toward booking or sharing contact info.
"""
    
    return base_prompt


def concierge_agent(state: State):
    """🚩 Dynamic agent with feature flag awareness"""
    prompt = build_concierge_prompt(state)
    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = concierge_model.invoke(messages)
    
    # 🚩 Track interaction count for potential auto-handoff
    interaction_count = state.get("interaction_count", 0) + 1
    
    return {
        "messages": [response],
        "interaction_count": interaction_count
    }


def listing_booking_agent(state: State):
    """🚩 Dynamic agent with feature flag awareness"""
    prompt = build_listing_booking_prompt(state)
    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = listing_booking_model.invoke(messages)
    return {"messages": [response]}


concierge_tool_node = ToolNode(concierge_tools)
listing_booking_tool_node = ToolNode(listing_booking_tools)

# =============================================================================
# ROUTING (Enhanced with flag-based logic)
# =============================================================================

def route_concierge(state: State) -> Literal["concierge_tools", "check_auto_handoff", "__end__"]:
    """🚩 Enhanced routing with auto-handoff check"""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "concierge_tools"
    
    # 🚩 Check if we should force handoff based on interaction count
    user_id = state.get("user_id", "")
    max_turns = 5  # Default
    
    # Could make this a flag too, but keeping it simple
    if state.get("interaction_count", 0) >= max_turns:
        logger.info(f"🔄 Auto-handoff triggered after {max_turns} interactions")
        return "check_auto_handoff"
    
    return "__end__"


def check_auto_handoff(state: State) -> Literal["listing_booking_agent", "__end__"]:
    """🚩 Decide whether to force handoff"""
    # In a real implementation, this would check if user has shown interest
    # For now, just pass through
    return "__end__"


def route_after_concierge_tools(state: State) -> Literal["concierge_agent", "listing_booking_agent"]:
    last = state["messages"][-1]
    content = str(getattr(last, "content", ""))

    # Tool output from handoff_to_listing_agent
    if "HANDOFF_LISTING:" in content:
        return "listing_booking_agent"
    
    # 🚩 Feature flag: Auto-handoff after showing listing details?
    user_id = state.get("user_id", "")
    if is_enabled("auto_handoff_after_details", user_id):
        # Check if get_listing_details was just called
        if hasattr(state["messages"][-2], "tool_calls"):
            for tool_call in state["messages"][-2].tool_calls:
                if tool_call.get("name") == "get_listing_details":
                    logger.info("🔄 Auto-handoff after listing details (feature flag enabled)")
                    return "listing_booking_agent"
    
    return "concierge_agent"


def route_listing_booking(state: State) -> Literal["listing_booking_tools", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "listing_booking_tools"
    return "__end__"


# =============================================================================
# GRAPH (Enhanced with feature flag nodes)
# =============================================================================

graph = (
    StateGraph(State)
    .add_node("concierge_agent", concierge_agent)
    .add_node("concierge_tools", concierge_tool_node)
    .add_node("check_auto_handoff", check_auto_handoff)  # 🚩 NEW
    .add_node("listing_booking_agent", listing_booking_agent)
    .add_node("listing_booking_tools", listing_booking_tool_node)
    .add_edge(START, "concierge_agent")
    .add_conditional_edges(
        "concierge_agent", 
        route_concierge, 
        ["concierge_tools", "check_auto_handoff", "__end__"]
    )
    .add_conditional_edges(
        "concierge_tools", 
        route_after_concierge_tools, 
        ["concierge_agent", "listing_booking_agent"]
    )
    .add_conditional_edges(
        "check_auto_handoff",
        check_auto_handoff,
        ["listing_booking_agent", "__end__"]
    )
    .add_conditional_edges(
        "listing_booking_agent", 
        route_listing_booking, 
        ["listing_booking_tools", "__end__"]
    )
    .add_edge("listing_booking_tools", "listing_booking_agent")
    .compile(name="Baton Concierge with Feature Flags")
)
