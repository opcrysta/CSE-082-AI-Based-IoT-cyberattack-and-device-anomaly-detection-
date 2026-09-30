"""
Telemetry Data Validation Module using Pydantic.
Validates incoming MQTT JSON payloads, handles missing or malformed fields gracefully,
and prevents corrupted data from crashing the downstream machine learning pipeline.
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError, ConfigDict


class TelemetryPayload(BaseModel):
    """
    Pydantic schema enforcing structure and physical constraints for IoT telemetry.
    Supports both our multi-device fleet and real-world TON_IoT sensor streams.
    """
    model_config = ConfigDict(extra="allow")  # Allow metadata fields without failing

    device_id: str = Field(..., min_length=1, description="Unique IoT Device Identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 formatted timestamp"
    )

    # Core Telemetry Features
    temperature: float = Field(..., ge=-40.0, le=125.0, description="Ambient or device temperature in Celsius")
    voltage: float = Field(default=230.0, ge=50.0, le=400.0, description="Operating voltage in Volts")
    cpu_usage: float = Field(default=15.0, ge=0.0, le=100.0, description="CPU utilization percentage")
    ram_usage: float = Field(default=40.0, ge=0.0, le=100.0, description="RAM utilization percentage")
    message_rate: float = Field(default=1.0, ge=0.0, le=200.0, description="Message publishing frequency in msg/sec")
    failed_auth_count: int = Field(default=0, ge=0, le=1000, description="Number of failed login attempts")
    network_latency: float = Field(default=15.0, ge=0.0, le=5000.0, description="Network round-trip latency in ms")

    # Optional Ground-Truth Metadata (when replaying labeled datasets)
    is_anomaly: Optional[int] = None
    attack_type: Optional[str] = None


class DataValidator:
    """
    Validates raw incoming MQTT payloads against the TelemetryPayload schema.
    """

    @staticmethod
    def validate_json_string(raw_payload: str) -> Tuple[bool, Optional[TelemetryPayload], Optional[str]]:
        """
        Parses a raw UTF-8 JSON string and validates it against TelemetryPayload.

        Returns:
            (is_valid: bool, validated_obj: Optional[TelemetryPayload], error_message: Optional[str])
        """
        if not raw_payload or not raw_payload.strip():
            return False, None, "Empty payload received"

        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError as err:
            return False, None, f"Malformed JSON: {str(err)}"

        return DataValidator.validate_dict(data)

    @staticmethod
    def validate_dict(data: Dict[str, Any]) -> Tuple[bool, Optional[TelemetryPayload], Optional[str]]:
        """
        Validates a Python dictionary against the TelemetryPayload schema.
        """
        if not isinstance(data, dict):
            return False, None, f"Expected JSON object, got {type(data).__name__}"

        try:
            payload_obj = TelemetryPayload(**data)
            return True, payload_obj, None
        except ValidationError as err:
            # Produce a clean, single-line error summary
            error_details = "; ".join([f"{e['loc'][0]}: {e['msg']}" for e in err.errors()])
            return False, None, f"Schema validation error ({error_details})"
