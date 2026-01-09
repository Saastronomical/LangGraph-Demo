# Feature Flags Demo Guide

## For Interview with Wally

### Quick Demo (3 minutes)

**Terminal Demo:**

```bash
# 1. Show default behavior
python demo_flags.py

# 2. Show 50% rollout
FF_AGGRESSIVE_CAPTURE=50 python demo_flags.py

# 3. Show kill switch
FF_SHOW_RISKS_UPFRONT=false python demo_flags.py

# 4. Show status
python -c "from src.feature_flags import get_feature_flags_status; print(get_feature_flags_status())"
```

### What to Say to Wally

**Opening (30 seconds):**
> "I added production feature flags to the demo because you explicitly mentioned 'shipping behind feature flags' in the job description. This lets Baton A/B test agent behavior and do gradual rollouts without code deploys."

**Show the demo (2 minutes):**

1. **Run `python demo_flags.py`**
   - "See how different users get different experiences deterministically"
   - "This shows 50% rollout - same user always gets same result"

2. **Show config file `feature_flags.json`**
   - "Product team can adjust these without touching code"
   - "Example: test if showing risks scares buyers"

3. **Show kill switch**
   ```bash
   FF_SHOW_RISKS_UPFRONT=false python demo_flags.py
   ```
   - "If conversion drops, instant disable - no deploy needed"

**Real-world scenario (30 seconds):**
> "For example, Baton could test two agent tones: 'professional' vs 'consultative'. Run 50/50 for a week, measure which converts better, then roll out the winner. Or ship a new lead capture flow to 10% of users, verify it works, then gradually increase to 100%."

### Key Points to Emphasize

1. **"I read the job description"** - This directly addresses "shipping behind feature flags"

2. **"Production thinking"** - Not just building features, but deploying them safely

3. **"Baton-specific flags"** - These aren't generic; they're for their actual use cases:
   - Lead capture strategy
   - Agent routing logic  
   - Information disclosure

4. **"No external dependencies"** - Works with their stack, no LaunchDarkly subscription needed

### If He Asks Technical Questions

**"How does the 50% rollout work?"**
> "Deterministic hash of user_id + flag_name. Same user always gets same result for consistent experience. Hash mod 100 gives 0-99, compare to rollout percentage."

**"How would you use this in production?"**
> "Three ways: (1) JSON config file for product team, (2) Environment variables for ops team, (3) Admin API for dynamic changes. I'd export evaluations to analytics to measure conversion by variant."

**"What about performance?"**
> "O(1) hash lookups, no database queries. Negligible latency - under 1ms per check. Flag state is in-memory."

**"How do you prevent flag sprawl?"**
> "Time-box flags. Once a feature is stable at 100%, remove the flag in next sprint. Keep the config clean."

### Files to Have Open

1. **`demo_flags.py`** - The demo script
2. **`feature_flags.json`** - The config
3. **`src/feature_flags.py`** - Show the hash function if he's curious
4. **`README_FEATURE_FLAGS.md`** - Comprehensive docs

### Backup: Show in LangGraph Studio

If you want to show it working with actual agents:

```bash
# 1. Set flag
export FF_AGGRESSIVE_CAPTURE=true

# 2. Run LangGraph
langgraph dev

# 3. In Studio, show how agent behavior changes
# Compare control user vs variant user side-by-side
```

### Close

**Wrap up (15 seconds):**
> "This is working code that shows I understand modern deployment practices. Happy to discuss how Baton would extend this - maybe segment targeting by user type, or time-based auto-rollout."

---

## Quick Reference

**Demo commands:**
```bash
python demo_flags.py                           # Full demo
FF_AGGRESSIVE_CAPTURE=50 python demo_flags.py  # 50% rollout
FF_SHOW_RISKS_UPFRONT=false python demo_flags.py  # Kill switch
```

**Key files:**
- `demo_flags.py` - Interactive demo
- `src/feature_flags.py` - Flag system (320 lines)
- `src/graph_with_flags.py` - Enhanced agents
- `feature_flags.json` - Config example
- `README_FEATURE_FLAGS.md` - Full docs
