"""
Sleep timer command module for Dyson2MQTT app.
"""

import logging
import re
from typing import Union

from blowcontrol.mqtt.client import DysonMQTTClient

logger = logging.getLogger(__name__)


def parse_sleep_time(value: Union[str, int]) -> int:
    """
    Parse sleep timer value from flexible formats:
    - raw minutes (int or str)
    - '2h15m', '2:15', '1h', '45m', etc.
    Returns minutes as int.
    Raises ValueError for invalid input.
    """
    if isinstance(value, int):
        minutes = value
        if minutes < 0 or minutes > 540:
            raise ValueError("Sleep timer must be between 0 and 540 minutes (0 = off).")
        return minutes

    if not isinstance(value, str):
        raise ValueError(f"Invalid type for sleep timer: {type(value)}")

    s = value.strip().lower()
    if s == "off":
        return 0

    # 2:15 or 1:05
    if ":" in s:
        parts = s.split(":")
        if (
            len(parts) == 2
            and parts[0].isdigit()
            and parts[1].isdigit()
            and 0 <= int(parts[1]) < 60
        ):
            minutes = int(parts[0]) * 60 + int(parts[1])
            if minutes < 0 or minutes > 540:
                raise ValueError(
                    "Sleep timer must be between 0 and 540 minutes (0 = off)."
                )
            return minutes
        raise ValueError(f"Invalid time format: {value}")

    # 2h15m or 1h or 45m (strict: only allow h then m, not mixed or out of order)
    if re.fullmatch(r"(\d+h)?(\d+m)?", s):
        hours = 0
        mins = 0
        h_match = re.match(r"(\d+)h", s)
        m_match = re.search(r"(\d+)m", s)
        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            mins = int(m_match.group(1))
        if hours == 0 and mins == 0:
            raise ValueError(f"Invalid time format: {value}")
        minutes = hours * 60 + mins
        if minutes < 0 or minutes > 540:
            raise ValueError("Sleep timer must be between 0 and 540 minutes (0 = off).")
        return minutes

    # raw minutes as string
    if s.isdigit():  # type: ignore[unreachable]
        minutes = int(s)
        if minutes < 0 or minutes > 540:
            raise ValueError("Sleep timer must be between 0 and 540 minutes (0 = off).")
        return minutes

    raise ValueError(f"Invalid time format: {value}")


def set_sleep_timer(value: Union[str, int]) -> bool:
    """
    Set the Dyson device sleep timer (0-540 minutes, flexible input).
    0 or "off" will clear the timer.
    Returns True if successful, False otherwise.
    """
    try:
        minutes = parse_sleep_time(value)
        client = DysonMQTTClient(client_id="d2mqtt-cmd")
        client.connect()

        if minutes == 0:
            client.set_numeric_state("sltm", "OFF")
        else:
            minutes_str = f"{minutes:04d}"
            client.set_numeric_state("sltm", minutes_str)

        client.disconnect()
        return True
    except Exception as e:
        logger.error(f"Failed to set sleep timer: {e}")
        return False
