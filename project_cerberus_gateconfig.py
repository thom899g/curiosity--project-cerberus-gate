"""
CERBERUS GATE Configuration Module
Architecture Rationale: Centralized configuration with environment-based overrides
ensures deployment flexibility while maintaining type safety.
"""
import os
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Initialize logging BEFORE any other operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelemetryTier(Enum):
    """Marketable data richness tiers"""
    RAW_LOGS = "raw_logs"           # Basic stream: anonymized logs only
    ANNOTATED_FAILURES = "annotated_failures"  # + failure transitions with metadata
    STRATEGY_OVERRIDES = "strategy_overrides"  # + full strategy decision logs
    PREMIUM = "premium"            # All data + predictive analytics
    
    @classmethod
    def from_string(cls, tier_str: str) -> 'TelemetryTier':
        try:
            return cls(tier_str)
        except ValueError:
            logger.warning(f"Invalid tier string {tier_str}, defaulting to RAW_LOGS")
            return cls.RAW_LOGS

@dataclass
class StressThresholds:
    """System stress state detection parameters"""
    RAM_THRESHOLD: float = 0.95  # 95% RAM usage triggers collection
    PNL_NEGATIVE: bool = True    # Negative PnL triggers collection
    CPU_IDLE_THRESHOLD: float = 0.66  # 66% idle cycles available
    
    def is_stressed_state(self, ram_usage: float, pnl_status: str) -> bool:
        """Determine if system is in high-stress state for telemetry capture"""
        try:
            pnl_negative = pnl_status.lower() == "negative"
            return ram_usage >= self.RAM_THRESHOLD and pnl_negative
        except (AttributeError, ValueError) as e:
            logger.error(f"Error evaluating stress state: {e}")
            return False

@dataclass
class FirebaseConfig:
    """Firebase connection and schema configuration"""
    PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "cerberus-gate-prod")
    CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS", "./firebase_credentials.json")
    
    # Collection names for Firestore
    COLLECTIONS = {
        "telemetry_stream": "cerberus_telemetry",
        "subscribers": "cerberus_subscribers",
        "anonymization_rules": "cerberus_anonymization",
        "system_state": "cerberus_system_state"
    }
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not os.path.exists(self.CREDENTIALS_PATH):
            logger.critical(f"Firebase credentials not found at {self.CREDENTIALS_PATH}")
            return False
        return True

@dataclass
class EncryptionConfig:
    """Data encryption and anonymization settings"""
    AES_KEY_SIZE: int = 256
    ANONYMIZATION_SALT: str = os.getenv("ANONYMIZATION_SALT", "cerberus-salt-2024")
    # Rotate keys every 24 hours for security
    KEY_ROTATION_HOURS: int = 24
    
    @staticmethod
    def generate_encryption_key() -> bytes:
        """Generate secure encryption key"""
        import secrets
        return secrets.token_bytes(32)

@dataclass
class MonetizationConfig:
    """Pricing and tier configuration"""
    TIER_PRICES: Dict[TelemetryTier, float] = None
    
    def __post_init__(self):
        if self.TIER_PRICES is None:
            self.TIER_PRICES = {
                TelemetryTier.RAW_LOGS: 99.00,
                TelemetryTier.ANNOTATED_FAILURES: 299.00,
                TelemetryTier.STRATEGY_OVERRIDES: 799.00,
                TelemetryTier.PREMIUM: 1499.00
            }
    
    def get_tier_price(self, tier: TelemetryTier) -> float:
        """Get price for specific tier with error handling"""
        try:
            return self.TIER_PRICES[tier]
        except KeyError:
            logger.warning(f"Price not found for tier {tier}, using RAW_LOGS price")
            return self.TIER_PRICES[TelemetryTier.RAW_LOGS]

class CerberusConfig:
    """Main configuration aggregator"""
    
    def __init__(self):
        self.stress_thresholds = StressThresholds()
        self.firebase = FirebaseConfig()
        self.encryption = EncryptionConfig()
        self.monetization = MonetizationConfig()
        
        # Runtime state tracking
        self._initialized = False
        
        # Validate critical configurations
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate all configuration components"""
        errors = []
        
        # Check Firebase credentials
        if not self.firebase.validate():
            errors.append("Firebase configuration invalid")
        
        # Check environment variables for production
        if not os.getenv("ANONYMIZATION_SALT"):
            logger.warning("ANONYMIZATION_SALT not set, using default (not secure for production)")
        
        if errors:
            error_msg = f"Configuration errors: {', '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self._initialized = True
        logger.info("CERBERUS GATE configuration validated successfully")

# Global configuration instance
config = CerberusConfig()