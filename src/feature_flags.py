"""
Production Feature Flag System for Baton AI Agents

Supports:
- Percentage-based rollouts (10% → 50% → 100%)
- User targeting (beta users, specific advisors)
- Kill switches (instant disable without deploy)
- A/B testing variants
- Audit logging

Usage:
    flags = FeatureFlagManager()
    
    # Simple check
    if flags.is_enabled("aggressive_capture", user_id="user_123"):
        # Use aggressive capture logic
    
    # Get variant for A/B test
    tone = flags.get_variant("agent_tone", user_id="user_123")  # "professional" or "casual"
    
    # Check with context
    if flags.is_enabled("show_risks", user_id="user_123", context={"listing_status": "under_contract"}):
        # Show risks
"""

import os
import json
import hashlib
import logging
from typing import Any, Literal
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger("FeatureFlags")


@dataclass
class FlagConfig:
    """Configuration for a single feature flag"""
    name: str
    enabled: bool = False
    rollout_percentage: int = 0  # 0-100
    target_users: list[str] = None  # Specific user IDs
    target_segments: list[str] = None  # e.g., ["beta_users", "premium"]
    variant: str | None = None  # For A/B testing
    description: str = ""
    
    def __post_init__(self):
        if self.target_users is None:
            self.target_users = []
        if self.target_segments is None:
            self.target_segments = []


class FeatureFlagManager:
    """
    Production feature flag system with targeting and gradual rollout.
    
    This is what companies like LaunchDarkly/Optimizely do, but simplified.
    """
    
    def __init__(self, config_path: str | None = None):
        """
        Args:
            config_path: Path to JSON config file. If None, uses defaults + env overrides.
        """
        self.flags: dict[str, FlagConfig] = {}
        self.audit_log: list[dict] = []
        
        # Load default flags
        self._load_defaults()
        
        # Override from config file if provided
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
        
        # Override from environment variables
        self._load_from_env()
    
    def _load_defaults(self):
        """Define default feature flags for Baton AI agents"""
        
        # Lead capture strategy flags
        self.flags["aggressive_capture"] = FlagConfig(
            name="aggressive_capture",
            enabled=False,
            rollout_percentage=0,
            description="Ask for contact info after first listing detail request (vs waiting for explicit interest)"
        )
        
        self.flags["require_both_contacts"] = FlagConfig(
            name="require_both_contacts",
            enabled=False,
            rollout_percentage=0,
            description="Require BOTH email AND phone (vs current email OR phone logic)"
        )
        
        self.flags["collect_budget_upfront"] = FlagConfig(
            name="collect_budget_upfront",
            enabled=False,
            rollout_percentage=0,
            description="Ask about budget/timeline before showing listings"
        )
        
        # Information disclosure flags
        self.flags["show_risks_upfront"] = FlagConfig(
            name="show_risks_upfront",
            enabled=True,
            rollout_percentage=100,
            description="Include risk analysis in listing details"
        )
        
        self.flags["show_comparables"] = FlagConfig(
            name="show_comparables",
            enabled=True,
            rollout_percentage=100,
            description="Show comparable sales data in listing details"
        )
        
        self.flags["early_advisor_intro"] = FlagConfig(
            name="early_advisor_intro",
            enabled=False,
            rollout_percentage=0,
            description="Offer advisor connection in Concierge agent (vs only in Booking agent)"
        )
        
        # Agent routing flags
        self.flags["auto_handoff_after_details"] = FlagConfig(
            name="auto_handoff_after_details",
            enabled=True,
            rollout_percentage=100,
            description="Automatically hand off to Booking agent after showing listing details"
        )
        
        self.flags["skip_concierge_returning"] = FlagConfig(
            name="skip_concierge_returning",
            enabled=False,
            rollout_percentage=0,
            description="Skip Concierge for users who have previously viewed listings"
        )
        
        # Search & discovery flags
        self.flags["enable_vector_search"] = FlagConfig(
            name="enable_vector_search",
            enabled=True,
            rollout_percentage=100,
            description="Use semantic vector search (vs keyword fallback only)"
        )
        
        self.flags["show_under_contract"] = FlagConfig(
            name="show_under_contract",
            enabled=True,
            rollout_percentage=100,
            description="Include under-contract listings in search results (for social proof)"
        )
        
        # A/B test variants
        self.flags["agent_tone"] = FlagConfig(
            name="agent_tone",
            enabled=True,
            rollout_percentage=100,
            variant="professional",  # vs "casual" or "consultative"
            description="Agent personality variant for A/B testing"
        )
    
    def _load_from_file(self, path: str):
        """Load flag overrides from JSON config file"""
        try:
            with open(path, 'r') as f:
                config = json.load(f)
                for name, data in config.items():
                    if name in self.flags:
                        # Update existing flag
                        for key, value in data.items():
                            setattr(self.flags[name], key, value)
                    else:
                        # Create new flag
                        self.flags[name] = FlagConfig(name=name, **data)
            logger.info(f"✅ Loaded feature flags from {path}")
        except Exception as e:
            logger.error(f"❌ Failed to load flags from {path}: {e}")
    
    def _load_from_env(self):
        """
        Override flags from environment variables.
        Format: FF_<FLAG_NAME>=true|false|<percentage>
        Example: FF_AGGRESSIVE_CAPTURE=true or FF_AGGRESSIVE_CAPTURE=50
        """
        for key, value in os.environ.items():
            if not key.startswith("FF_"):
                continue
            
            flag_name = key[3:].lower()
            if flag_name not in self.flags:
                continue
            
            value = value.strip().lower()
            
            # Boolean override
            if value in ("true", "1", "on"):
                self.flags[flag_name].enabled = True
                self.flags[flag_name].rollout_percentage = 100
            elif value in ("false", "0", "off"):
                self.flags[flag_name].enabled = False
                self.flags[flag_name].rollout_percentage = 0
            # Percentage override
            elif value.isdigit():
                pct = int(value)
                if 0 <= pct <= 100:
                    self.flags[flag_name].enabled = True
                    self.flags[flag_name].rollout_percentage = pct
    
    def is_enabled(
        self,
        flag_name: str,
        user_id: str | None = None,
        context: dict[str, Any] | None = None
    ) -> bool:
        """
        Check if a feature flag is enabled for a given user.
        
        Args:
            flag_name: Name of the flag
            user_id: User identifier (e.g., session ID, email hash)
            context: Additional context for targeting (e.g., {"listing_status": "under_contract"})
        
        Returns:
            True if flag is enabled for this user
        """
        if flag_name not in self.flags:
            logger.warning(f"⚠️ Unknown flag: {flag_name}")
            return False
        
        flag = self.flags[flag_name]
        
        # Global kill switch
        if not flag.enabled:
            return False
        
        # Explicit user targeting
        if user_id and user_id in flag.target_users:
            self._log_evaluation(flag_name, user_id, True, "targeted_user")
            return True
        
        # Percentage-based rollout
        if flag.rollout_percentage == 100:
            return True
        elif flag.rollout_percentage == 0:
            return False
        else:
            # Deterministic hash-based rollout
            # Same user always gets same result for consistent experience
            if user_id:
                user_hash = self._hash_user(flag_name, user_id)
                enabled = user_hash < flag.rollout_percentage
                self._log_evaluation(flag_name, user_id, enabled, f"rollout_{flag.rollout_percentage}%")
                return enabled
            else:
                # No user_id: treat as random sample
                import random
                return random.randint(0, 99) < flag.rollout_percentage
    
    def get_variant(
        self,
        flag_name: str,
        user_id: str | None = None,
        default: str = "control"
    ) -> str:
        """
        Get A/B test variant for a flag.
        
        Args:
            flag_name: Name of the flag
            user_id: User identifier
            default: Default variant if flag disabled
        
        Returns:
            Variant name (e.g., "professional", "casual")
        """
        if not self.is_enabled(flag_name, user_id):
            return default
        
        flag = self.flags[flag_name]
        return flag.variant or default
    
    def _hash_user(self, flag_name: str, user_id: str) -> int:
        """
        Deterministic hash for consistent rollout.
        Same user gets same result, but different flags can have different rollouts.
        
        Returns: Integer 0-99
        """
        combined = f"{flag_name}:{user_id}"
        hash_bytes = hashlib.md5(combined.encode()).digest()
        # Use first 4 bytes as integer, mod 100
        hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
        return hash_int % 100
    
    def _log_evaluation(self, flag_name: str, user_id: str, result: bool, reason: str):
        """Log flag evaluation for analytics"""
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "flag": flag_name,
            "user_id": user_id,
            "result": result,
            "reason": reason
        })
        
        # Keep last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    def get_all_flags(self) -> dict[str, dict]:
        """Get current state of all flags (for admin dashboard)"""
        return {
            name: asdict(flag)
            for name, flag in self.flags.items()
        }
    
    def export_audit_log(self) -> list[dict]:
        """Export audit log for analytics"""
        return self.audit_log.copy()
    
    def update_flag(
        self,
        flag_name: str,
        enabled: bool | None = None,
        rollout_percentage: int | None = None,
        target_users: list[str] | None = None
    ):
        """
        Dynamically update flag configuration (for gradual rollout).
        In production, this would be driven by an admin API.
        """
        if flag_name not in self.flags:
            logger.warning(f"⚠️ Cannot update unknown flag: {flag_name}")
            return
        
        flag = self.flags[flag_name]
        
        if enabled is not None:
            flag.enabled = enabled
        if rollout_percentage is not None:
            flag.rollout_percentage = max(0, min(100, rollout_percentage))
        if target_users is not None:
            flag.target_users = target_users
        
        logger.info(f"🔧 Updated {flag_name}: enabled={flag.enabled}, rollout={flag.rollout_percentage}%")


# =============================================================================
# CONVENIENCE FUNCTIONS FOR AGENT INTEGRATION
# =============================================================================

# Global singleton
_flag_manager: FeatureFlagManager | None = None


def get_flag_manager() -> FeatureFlagManager:
    """Get or create global flag manager"""
    global _flag_manager
    if _flag_manager is None:
        config_path = os.getenv("FEATURE_FLAGS_CONFIG")
        _flag_manager = FeatureFlagManager(config_path)
    return _flag_manager


def is_enabled(flag_name: str, user_id: str | None = None, context: dict | None = None) -> bool:
    """Convenience function for checking flags"""
    return get_flag_manager().is_enabled(flag_name, user_id, context)


def get_variant(flag_name: str, user_id: str | None = None, default: str = "control") -> str:
    """Convenience function for A/B test variants"""
    return get_flag_manager().get_variant(flag_name, user_id, default)


# =============================================================================
# ADMIN TOOL FOR AGENTS (Optional)
# =============================================================================

def get_feature_flags_status() -> str:
    """
    Tool that returns current feature flag status.
    Useful for debugging or showing users what's enabled.
    """
    flags = get_flag_manager().get_all_flags()
    
    enabled = [name for name, config in flags.items() if config["enabled"]]
    disabled = [name for name, config in flags.items() if not config["enabled"]]
    
    output = "🚩 FEATURE FLAGS STATUS\n\n"
    output += "ENABLED:\n"
    for name in enabled:
        config = flags[name]
        output += f"  ✅ {name} ({config['rollout_percentage']}% rollout)\n"
        if config['description']:
            output += f"     {config['description']}\n"
    
    output += "\nDISABLED:\n"
    for name in disabled:
        config = flags[name]
        output += f"  ❌ {name}\n"
        if config['description']:
            output += f"     {config['description']}\n"
    
    return output


# =============================================================================
# EXAMPLE USAGE IN GRAPH.PY
# =============================================================================

if __name__ == "__main__":
    # Demo
    flags = FeatureFlagManager()
    
    print("\n" + "="*60)
    print("FEATURE FLAG DEMO")
    print("="*60 + "\n")
    
    # Example 1: Simple check
    user_id = "test_user_123"
    
    print(f"User: {user_id}\n")
    
    print("1. Aggressive capture (0% rollout):")
    print(f"   Enabled: {flags.is_enabled('aggressive_capture', user_id)}\n")
    
    print("2. Show risks (100% rollout):")
    print(f"   Enabled: {flags.is_enabled('show_risks_upfront', user_id)}\n")
    
    # Example 2: Gradual rollout
    print("3. Testing 50% rollout:")
    flags.update_flag("aggressive_capture", enabled=True, rollout_percentage=50)
    
    results = {"enabled": 0, "disabled": 0}
    for i in range(100):
        test_user = f"user_{i}"
        if flags.is_enabled("aggressive_capture", test_user):
            results["enabled"] += 1
        else:
            results["disabled"] += 1
    
    print(f"   Out of 100 users: {results['enabled']} enabled, {results['disabled']} disabled")
    print(f"   (Should be ~50/50)\n")
    
    # Example 3: A/B testing
    print("4. A/B test variant:")
    tone = flags.get_variant("agent_tone", user_id)
    print(f"   User {user_id} gets tone: {tone}\n")
    
    # Example 4: Targeted users
    print("5. Targeted beta users:")
    flags.update_flag("collect_budget_upfront", enabled=True, target_users=["beta_user_1", "beta_user_2"])
    print(f"   Beta user: {flags.is_enabled('collect_budget_upfront', 'beta_user_1')}")
    print(f"   Regular user: {flags.is_enabled('collect_budget_upfront', 'regular_user')}\n")
    
    # Example 5: Status report
    print(get_feature_flags_status())
