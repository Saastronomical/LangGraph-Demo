#!/usr/bin/env python3
"""
Feature Flags Demo - Run this to see flags in action

Usage:
    python demo_flags.py
    
    # Or test specific scenarios:
    FF_AGGRESSIVE_CAPTURE=50 python demo_flags.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from feature_flags import FeatureFlagManager, get_flag_manager

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def demo_basic_flags():
    """Show basic flag checking"""
    print_section("1. BASIC FLAG CHECKING")
    
    flags = get_flag_manager()
    user_id = "demo_user_123"
    
    print(f"Testing user: {user_id}\n")
    
    # Check various flags
    checks = [
        ("aggressive_capture", "Ask for contact info early"),
        ("show_risks_upfront", "Show risk analysis in listings"),
        ("require_both_contacts", "Require email AND phone"),
        ("early_advisor_intro", "Offer advisor in Concierge agent"),
    ]
    
    for flag_name, description in checks:
        enabled = flags.is_enabled(flag_name, user_id)
        status = "✅ ENABLED" if enabled else "❌ DISABLED"
        print(f"{status}: {flag_name}")
        print(f"   → {description}\n")

def demo_gradual_rollout():
    """Show percentage-based rollout"""
    print_section("2. GRADUAL ROLLOUT (50%)")
    
    flags = get_flag_manager()
    
    # Enable a flag at 50%
    print("Setting 'aggressive_capture' to 50% rollout...\n")
    flags.update_flag("aggressive_capture", enabled=True, rollout_percentage=50)
    
    # Test 20 different users
    enabled_count = 0
    disabled_count = 0
    
    print("Testing 20 different users:")
    for i in range(20):
        user_id = f"user_{i:03d}"
        enabled = flags.is_enabled("aggressive_capture", user_id)
        
        if enabled:
            enabled_count += 1
            print(f"  user_{i:03d}: ✅ sees aggressive capture")
        else:
            disabled_count += 1
            print(f"  user_{i:03d}: ❌ sees normal flow")
    
    print(f"\nResult: {enabled_count} enabled, {disabled_count} disabled")
    print(f"Expected: ~10 enabled, ~10 disabled (50% rollout)")
    
    # Show consistency
    print("\n" + "-"*70)
    print("Testing consistency (same user, multiple checks):")
    test_user = "user_005"
    for check in range(3):
        enabled = flags.is_enabled("aggressive_capture", test_user)
        print(f"  Check {check+1}: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
    print(f"\n✨ Same result every time - users get consistent experience")

def demo_ab_testing():
    """Show A/B test variants"""
    print_section("3. A/B TESTING (Agent Tone)")
    
    flags = get_flag_manager()
    
    print("Testing agent tone variants for different users:\n")
    
    test_users = [
        "buyer_alice",
        "buyer_bob", 
        "buyer_charlie",
        "buyer_diana",
        "buyer_eve"
    ]
    
    for user_id in test_users:
        tone = flags.get_variant("agent_tone", user_id)
        print(f"  {user_id:15s} → {tone.upper()} tone")
    
    print("\n💡 In production, you'd measure which tone converts better")

def demo_targeted_users():
    """Show beta user targeting"""
    print_section("4. TARGETED BETA USERS")
    
    flags = get_flag_manager()
    
    # Target specific users for beta feature
    beta_users = ["vip_user_1", "internal_tester", "founder"]
    flags.update_flag(
        "collect_budget_upfront",
        enabled=True,
        rollout_percentage=0,  # 0% for general population
        target_users=beta_users
    )
    
    print("Feature: collect_budget_upfront")
    print(f"Rollout: 0% (but enabled for specific users)\n")
    print("Beta testers:")
    for user in beta_users:
        print(f"  ✅ {user}")
    
    print("\nTesting access:")
    test_users = ["vip_user_1", "regular_user_abc", "internal_tester", "random_visitor"]
    for user_id in test_users:
        enabled = flags.is_enabled("collect_budget_upfront", user_id)
        status = "✅ HAS ACCESS" if enabled else "❌ NO ACCESS"
        is_beta = " (beta tester)" if user_id in beta_users else ""
        print(f"  {status}: {user_id}{is_beta}")

def demo_kill_switch():
    """Show instant disable (kill switch)"""
    print_section("5. KILL SWITCH (Emergency Disable)")
    
    flags = get_flag_manager()
    user_id = "test_user"
    
    # Enable a feature
    print("Scenario: 'show_risks_upfront' is causing conversion drop\n")
    print("Step 1: Feature is live at 100%")
    flags.update_flag("show_risks_upfront", enabled=True, rollout_percentage=100)
    print(f"  User sees risks: {flags.is_enabled('show_risks_upfront', user_id)}")
    
    print("\nStep 2: Product team notices issue, kills the feature")
    print("  Command: export FF_SHOW_RISKS_UPFRONT=false")
    flags.update_flag("show_risks_upfront", enabled=False)
    print(f"  User sees risks: {flags.is_enabled('show_risks_upfront', user_id)}")
    
    print("\n✨ No code deploy needed - instant rollback!")

def demo_agent_behavior():
    """Show how flags affect agent prompts"""
    print_section("6. AGENT BEHAVIOR CHANGES")
    
    from graph_with_flags import build_concierge_prompt, build_listing_booking_prompt
    
    flags = get_flag_manager()
    
    # Create two test users with different flag states
    state_control = {
        "user_id": "control_user",
        "messages": [],
        "interaction_count": 0
    }
    
    state_variant = {
        "user_id": "variant_user", 
        "messages": [],
        "interaction_count": 0
    }
    
    # Enable aggressive capture for variant user only
    flags.update_flag("aggressive_capture", enabled=True, target_users=["variant_user"])
    flags.update_flag("early_advisor_intro", enabled=True, target_users=["variant_user"])
    
    print("CONTROL USER (standard behavior):")
    print("-" * 70)
    control_prompt = build_concierge_prompt(state_control)
    # Show first 300 chars
    print(control_prompt[:300] + "...\n")
    
    print("VARIANT USER (with aggressive flags):")
    print("-" * 70)
    variant_prompt = build_concierge_prompt(state_variant)
    print(variant_prompt[:300] + "...\n")
    
    print("🚩 Notice the variant has extra instructions for aggressive behavior")

def demo_env_override():
    """Show environment variable override"""
    print_section("7. ENVIRONMENT VARIABLE OVERRIDE")
    
    print("Current environment flags:\n")
    
    env_flags = [
        ("FF_AGGRESSIVE_CAPTURE", "Aggressive lead capture"),
        ("FF_SHOW_RISKS_UPFRONT", "Show risk analysis"),
        ("FF_REQUIRE_BOTH_CONTACTS", "Require email + phone"),
    ]
    
    for env_var, description in env_flags:
        value = os.getenv(env_var, "not set")
        print(f"  {env_var}: {value}")
        print(f"    → {description}\n")
    
    print("💡 Try running: FF_AGGRESSIVE_CAPTURE=true python demo_flags.py")

def main():
    print("\n" + "🚩"*35)
    print("  BATON FEATURE FLAGS DEMO")
    print("🚩"*35)
    
    try:
        demo_basic_flags()
        demo_gradual_rollout()
        demo_ab_testing()
        demo_targeted_users()
        demo_kill_switch()
        demo_agent_behavior()
        demo_env_override()
        
        print("\n" + "="*70)
        print("  ✅ DEMO COMPLETE")
        print("="*70)
        print("\nNext steps:")
        print("  1. Try: FF_AGGRESSIVE_CAPTURE=50 python demo_flags.py")
        print("  2. Edit: feature_flags.json to change rollout percentages")
        print("  3. Run: langgraph dev  (to test in LangGraph Studio)")
        print("\n")
        
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you're in the project root directory:")
        print("  cd /path/to/LangGraph-Demo")
        print("  python demo_flags.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
