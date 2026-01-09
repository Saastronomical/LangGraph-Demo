# Feature Flags Integration for Baton AI Agents

## Overview

This implementation adds **production-grade feature flags** to the Baton two-agent system, enabling:

- **A/B testing** agent behavior without code changes
- **Gradual rollout** of new features (10% → 50% → 100%)
- **Kill switches** to instantly disable problematic features
- **Per-user targeting** for beta testing
- **Audit logging** for analytics

This is how companies like Stripe, Airbnb, and other fast-moving startups ship AI features safely.

---

## Quick Start

### 1. Environment Setup

```bash
# Optional: Load flags from config file
export FEATURE_FLAGS_CONFIG=feature_flags.json

# Override individual flags via environment
export FF_AGGRESSIVE_CAPTURE=true        # Force enable
export FF_SHOW_RISKS_UPFRONT=false       # Force disable
export FF_EARLY_ADVISOR_INTRO=50         # 50% rollout
```

### 2. Run the Enhanced Agent

```bash
# Use the new graph with feature flags
python graph_with_flags.py
```

### 3. Test Flag Behavior

```python
from feature_flags import get_flag_manager

flags = get_flag_manager()

# Check if enabled for a specific user
user_id = "session_abc123"
if flags.is_enabled("aggressive_capture", user_id):
    print("This user sees aggressive lead capture")

# Get A/B test variant
tone = flags.get_variant("agent_tone", user_id)
print(f"User gets {tone} tone")  # "professional" or "casual"
```

---

## Available Feature Flags

### Lead Capture Strategy

| Flag | Default | Description |
|------|---------|-------------|
| `aggressive_capture` | OFF | Ask for contact info after first listing detail view |
| `require_both_contacts` | OFF | Require BOTH email AND phone (vs email OR phone) |
| `collect_budget_upfront` | OFF | Ask about budget/timeline before showing listings |

**Use case:** Test which capture strategy converts better

---

### Information Disclosure

| Flag | Default | Description |
|------|---------|-------------|
| `show_risks_upfront` | ON | Include risk analysis in listing details |
| `show_comparables` | ON | Show comparable sales data |
| `early_advisor_intro` | OFF | Offer advisor connection in Concierge (vs only Booking agent) |

**Use case:** Test if showing risks reduces buyer confidence

---

### Agent Routing

| Flag | Default | Description |
|------|---------|-------------|
| `auto_handoff_after_details` | ON | Auto-transfer to Booking agent after listing details |
| `skip_concierge_returning` | OFF | Skip Concierge for repeat visitors |

**Use case:** Optimize conversion funnel by adjusting handoff timing

---

### Search & Discovery

| Flag | Default | Description |
|------|---------|-------------|
| `enable_vector_search` | ON | Use semantic search (vs keyword only) |
| `show_under_contract` | ON | Include sold deals for social proof |

**Use case:** Test if showing sold businesses builds credibility

---

### A/B Testing

| Flag | Variants | Description |
|------|----------|-------------|
| `agent_tone` | professional, casual, consultative | Agent personality |

**Use case:** Test which tone resonates better with buyers

---

## How It Works

### 1. Percentage-Based Rollout

Users are deterministically assigned to rollout groups via hash:

```python
# Same user always gets same result
flags.update_flag("aggressive_capture", enabled=True, rollout_percentage=25)

# User A: hash("aggressive_capture:user_a") % 100 = 17 → ENABLED
# User B: hash("aggressive_capture:user_b") % 100 = 43 → DISABLED
# User A on second visit: still 17 → ENABLED (consistent)
```

This enables gradual rollout: 10% → 25% → 50% → 100%

### 2. User Targeting

Beta test features with specific users:

```python
flags.update_flag(
    "collect_budget_upfront",
    enabled=True,
    target_users=["beta_user_1", "vip_client_abc"]
)

# Only these users see the feature, regardless of rollout %
```

### 3. Dynamic Agent Prompts

Agents adapt their behavior based on flag state:

```python
def build_concierge_prompt(state: State) -> str:
    user_id = state.get("user_id")
    
    # Get A/B test variant
    tone = get_variant("agent_tone", user_id)  # "professional" or "casual"
    
    # Check behavior flags
    if is_enabled("early_advisor_intro", user_id):
        prompt += "🚩 Proactively offer advisor connection after every response."
    
    if is_enabled("aggressive_capture", user_id):
        prompt += "🚩 Ask for contact info immediately after showing details."
    
    return prompt
```

### 4. Tool-Level Control

Tools respect flag state:

```python
def get_listing_details(listing_id: str, state: State) -> str:
    user_id = state.get("user_id")
    
    # Conditionally include risk analysis
    if is_enabled("show_risks_upfront", user_id):
        details += f"\nRisks: {listing['risks']}"
    
    # Conditionally include comparables
    if is_enabled("show_comparables", user_id):
        details += f"\n{listing['comparables']}"
    
    return details
```

---

## Real-World Usage Scenarios

### Scenario 1: A/B Test Lead Capture Strategy

**Goal:** Does aggressive capture (asking early) convert better than passive?

```bash
# Split traffic 50/50
export FF_AGGRESSIVE_CAPTURE=50

# Run for 1000 sessions, then check conversion:
# - Group A (aggressive): 50 conversions / 500 sessions = 10%
# - Group B (control): 35 conversions / 500 sessions = 7%
# Winner: Aggressive. Roll out to 100%.
```

### Scenario 2: Gradual Rollout of New Feature

**Goal:** Ship "budget collection" feature without breaking production

```bash
# Week 1: Beta users only
# (Set in feature_flags.json: target_users)

# Week 2: 10% rollout
export FF_COLLECT_BUDGET_UPFRONT=10

# Week 3: 50% rollout (no issues detected)
export FF_COLLECT_BUDGET_UPFRONT=50

# Week 4: Full rollout
export FF_COLLECT_BUDGET_UPFRONT=100
```

### Scenario 3: Kill Switch

**Problem:** "Show risks" feature is scaring buyers, conversion dropped 30%

```bash
# Instant disable (no code deploy)
export FF_SHOW_RISKS_UPFRONT=false

# Fix the messaging, then re-enable gradually
export FF_SHOW_RISKS_UPFRONT=25
```

---

## Integration with Existing Code

### Minimal Changes Required

The feature flag system integrates cleanly:

```python
# Before:
CONCIERGE_PROMPT = "You are Baton's concierge..."

# After:
def build_concierge_prompt(state):
    tone = get_variant("agent_tone", state["user_id"])
    return f"You are Baton's concierge. Tone: {tone}..."
```

### No Breaking Changes

- Original `graph.py` still works
- `graph_with_flags.py` is opt-in
- Feature flags default to current behavior

---

## Monitoring & Analytics

### Audit Log

Track which users see which features:

```python
flags = get_flag_manager()

# Get evaluation history
audit_log = flags.export_audit_log()

# Example entries:
# {
#   "timestamp": "2026-01-10T14:23:45Z",
#   "flag": "aggressive_capture",
#   "user_id": "session_abc",
#   "result": true,
#   "reason": "rollout_50%"
# }
```

### Flag Status Dashboard

```python
# Debug tool available to agents
show_feature_flags()

# Output:
# 🚩 FEATURE FLAGS STATUS
# 
# ENABLED:
#   ✅ aggressive_capture (50% rollout)
#      Ask for contact info after first detail view
#   ✅ show_risks_upfront (100% rollout)
#      Include risk analysis in listings
#
# DISABLED:
#   ❌ require_both_contacts
#      Require both email AND phone
```

---

## Configuration Files

### Option 1: JSON Config (Recommended)

```json
// feature_flags.json
{
  "aggressive_capture": {
    "enabled": true,
    "rollout_percentage": 25,
    "target_users": [],
    "description": "A/B test lead capture timing"
  }
}
```

Load via: `export FEATURE_FLAGS_CONFIG=feature_flags.json`

### Option 2: Environment Variables

```bash
export FF_AGGRESSIVE_CAPTURE=50      # 50% rollout
export FF_SHOW_RISKS_UPFRONT=false   # Force disable
export FF_AGENT_TONE=casual          # Override default
```

### Option 3: Programmatic Updates

```python
flags = get_flag_manager()
flags.update_flag("aggressive_capture", rollout_percentage=75)
```

---

## Production Considerations

### 1. User ID Strategy

Choose a consistent user identifier:

```python
# Option A: Session ID (anonymous)
state["user_id"] = f"session_{uuid.uuid4()}"

# Option B: Email hash (persistent across sessions)
state["user_id"] = hashlib.md5(user_email.encode()).hexdigest()

# Option C: Hybrid (logged in users + anonymous)
state["user_id"] = user.id if user.is_authenticated else f"anon_{session_id}"
```

**Recommendation:** Use email hash for logged-in users, session ID for anonymous

### 2. Performance Impact

- Flag checks are O(1) hash lookups
- No database queries required
- Deterministic hashing ensures consistency
- Negligible latency (<1ms per check)

### 3. Deployment Workflow

```bash
# 1. Ship code with flag DISABLED
git push origin main
# Flag defaults to OFF, no behavior change

# 2. Enable for beta users via config
# (No code deploy required)

# 3. Gradual rollout via env vars
# 10% → 25% → 50% → 100%

# 4. Remove flag after full rollout
# Clean up code once stable
```

---

## Advanced: Integration with Analytics

### Track Conversion by Flag Variant

```python
# When user converts
analytics.track("lead_captured", {
    "user_id": state["user_id"],
    "aggressive_capture": is_enabled("aggressive_capture", state["user_id"]),
    "agent_tone": get_variant("agent_tone", state["user_id"]),
    "timestamp": datetime.utcnow()
})

# Later: Group conversions by flag state
# SELECT agent_tone, COUNT(*) as conversions
# FROM analytics
# WHERE event = 'lead_captured'
# GROUP BY agent_tone
```

---

## Comparison to Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Feature Flags** (this) | No deploys for changes, gradual rollout, A/B testing | Requires user ID tracking |
| **Environment Variables** | Simple, built-in | All-or-nothing, requires deploy |
| **Code Comments** | Zero overhead | Can't change without deploy |
| **LaunchDarkly** | Full-featured, analytics | $$$, external dependency |

**This implementation:** LaunchDarkly-style system without the cost or complexity

---

## Demo for Interview

**Show Wally:**

1. **Live flag toggle:** Change `FF_AGGRESSIVE_CAPTURE=50` and show different users get different behavior
2. **A/B testing:** Demonstrate how you'd test agent tone variants
3. **Gradual rollout:** Explain 10% → 100% deployment strategy
4. **Kill switch:** Show instant disable of a feature

**Talk track:**
> "I built this because Baton needs to ship fast and iterate. With feature flags, we can:
> - Deploy code Friday, enable features Monday (after monitoring)
> - A/B test agent personalities without touching prompts
> - Kill broken features instantly without rollback
> - This is how Stripe ships 50+ times per day safely."

---

## Files

- `feature_flags.py` - Core flag system (320 lines)
- `graph_with_flags.py` - Enhanced agent with flag integration
- `feature_flags.json` - Example configuration
- `README_FEATURE_FLAGS.md` - This document

---

## Next Steps

1. **Add metrics export** - Send flag evaluations to analytics platform
2. **Admin API** - Build endpoint for non-engineers to toggle flags
3. **Segment targeting** - Enable flags based on user segment (e.g., "premium_buyers")
4. **Time-based rollout** - Auto-increase rollout % over time
5. **Multi-variate testing** - Test 3+ variants simultaneously

---

**Questions?** This is production-ready code that shows deep understanding of modern software deployment practices.
