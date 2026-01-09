"""
Baton Two-Agent System - Concierge + Listing/Booking with Smart Lookups
Flow update:
1) Concierge greets + can browse/list listings + offers advisor handoff
2) Listing/Booking agent gives deeper listing details + offers cal.com booking or advisor intro
3) When we have (name & email) OR (name & phone) (or all 3 + prefs), send webhook to Airtable
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
    LISTINGS,   # smart lookup
    ADVISORS,   # calendars + advisor names keyed by listing_id
)

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
# STATE
# =============================================================================

class State(TypedDict):
    messages: Annotated[list, add_messages]
    buyer_name: str
    buyer_email: str
    buyer_phone: str
    interested_listing: str
    lead_captured: bool


# =============================================================================
# CONCIERGE TOOLS (Agent 1)
# =============================================================================

def search_listings(query: str) -> str:
    """Search listings by any criteria."""
    logger.info(f"🔎 SEARCHING: {query}")
    results = vector_store.similarity_search(query, k=3)
    if not results:
        return "No matching listings found."
    return "\n\n---\n\n".join([str(doc.page_content).strip() for doc in results])


def list_all_listings() -> str:
    """Show summary of all available listings."""
    return str(get_listings_summary())


def get_listing_details(listing_id: str) -> str:
    """Get full details. Handles IDs OR Names."""
    logger.info(f"📄 DETAILS REQUESTED: {listing_id}")

    real_id = resolve_listing_id(listing_id)
    if not real_id:
        return f"Could not find a listing matching '{listing_id}'. Try searching by keyword or asking for the list of all listings."

    listing = LISTINGS[real_id]
    return f"""
**{listing['title']}** (ID: {real_id})
Asking: ${listing['asking_price']:,} | Cash Flow: ${listing['cash_flow']:,}
Multiple: {listing['multiple']}X

{listing['description']}

Risks: {', '.join(listing['risks'])}
""".strip()


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
) -> str:
    """
    Fire Airtable webhook when:
      - (name & email) OR (name & phone)
    Also accepts extra info like preferences.
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

    # ✅ SEND when name + (email OR phone)
    if has_name and (has_email or has_phone):
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
    if not (has_email or has_phone):
        missing.append("your email or phone number")

    return f"I’ve captured some info, but I still need {' and '.join(missing)} to submit this to the advisor."


# =============================================================================
# AGENTS
# =============================================================================

# Agent 1 tools: greet + browse + handoff
concierge_tools = [search_listings, list_all_listings, get_listing_details, handoff_to_listing_agent]

# Agent 2 tools: deeper details + booking + lead capture
listing_booking_tools = [get_listing_details, get_advisor_calendar, capture_contact_info]

concierge_model = ChatOpenAI(model="gpt-4o").bind_tools(concierge_tools)
listing_booking_model = ChatOpenAI(model="gpt-4o").bind_tools(listing_booking_tools)

CONCIERGE_PROMPT = """You are Baton’s M&A Concierge (Agent 1).

Your job:
- Greet the buyer warmly and quickly.
- You have access to listings and can search or show summaries.
- Always offer an option to connect them with an advisor.
- If the buyer expresses interest in a specific listing or asks for deeper details, call `handoff_to_listing_agent`
  with the listing ID or name immediately.

Behavior:
- Keep answers concise.
- After providing any listing info, ask: “Want me to connect you with the advisor for this deal?”
- If uncertain which listing they mean, ask a short clarifying question OR use `search_listings`.
"""

LISTING_BOOKING_PROMPT = """You are Baton’s Listing + Booking Agent (Agent 2).

Your job:
- Provide deeper details on the listing (use `get_listing_details` if needed).
- Offer two CTAs:
  1) Book a call via cal.com (use `get_advisor_calendar`)
  2) Get connected to an advisor by capturing contact info (use `capture_contact_info`)

Lead capture rule:
- The moment you have (name & email) OR (name & phone), call `capture_contact_info`.
- If you have extra info (preferences, timeline, budget range), include it in `preferences`.

Tone:
- Crisp and helpful.
- Don’t overtalk. Move the user toward booking or sharing contact info.
"""


def concierge_agent(state: State):
    messages = [SystemMessage(content=CONCIERGE_PROMPT)] + state["messages"]
    response = concierge_model.invoke(messages)
    return {"messages": [response]}


def listing_booking_agent(state: State):
    messages = [SystemMessage(content=LISTING_BOOKING_PROMPT)] + state["messages"]
    response = listing_booking_model.invoke(messages)
    return {"messages": [response]}


concierge_tool_node = ToolNode(concierge_tools)
listing_booking_tool_node = ToolNode(listing_booking_tools)

# =============================================================================
# ROUTING
# =============================================================================

def route_concierge(state: State) -> Literal["concierge_tools", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "concierge_tools"
    return "__end__"


def route_after_concierge_tools(state: State) -> Literal["concierge_agent", "listing_booking_agent"]:
    last = state["messages"][-1]
    content = str(getattr(last, "content", ""))

    # Tool output from handoff_to_listing_agent
    if "HANDOFF_LISTING:" in content:
        return "listing_booking_agent"
    return "concierge_agent"


def route_listing_booking(state: State) -> Literal["listing_booking_tools", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "listing_booking_tools"
    return "__end__"


# =============================================================================
# GRAPH
# =============================================================================

graph = (
    StateGraph(State)
    .add_node("concierge_agent", concierge_agent)
    .add_node("concierge_tools", concierge_tool_node)
    .add_node("listing_booking_agent", listing_booking_agent)
    .add_node("listing_booking_tools", listing_booking_tool_node)
    .add_edge(START, "concierge_agent")
    .add_conditional_edges("concierge_agent", route_concierge, ["concierge_tools", "__end__"])
    .add_conditional_edges("concierge_tools", route_after_concierge_tools, ["concierge_agent", "listing_booking_agent"])
    .add_conditional_edges("listing_booking_agent", route_listing_booking, ["listing_booking_tools", "__end__"])
    .add_edge("listing_booking_tools", "listing_booking_agent")
    .compile(name="Baton Concierge v2")
)
