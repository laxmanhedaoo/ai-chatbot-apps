import ast
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from livekit import api

from models.prospect import Prospect
from repository.prospect_repository import get_prospect_from_db, save_prospect_to_db
from utils.agent_utils.voice_catalog import get_default_voice, get_language_locale
from utils.config_utils.config_loader import get_config
from utils.config_utils.env_loader import get_env_var
from utils.monitoring_utils.logging import get_logger

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

logger = get_logger("outbound-calling")

LIVEKIT_API_KEY = get_config("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = get_config("LIVEKIT_API_SECRET")
LIVEKIT_URL = get_config("LIVEKIT_URL", default="wss://livekit.example.com", required=False)
OUTBOUND_TRUNK_ID = get_env_var("SIP_OUTBOUND_TRUNK_ID")
AGENT_NAME = "outbound-caller"
DEFAULT_PROSPECT_ID = "f2a45c3c-22f9-4d2f-9a87-b9f7a07b9e8c"
PHONE_PARTICIPANT_IDENTITY = "phone_user"

ACTIVE_PARTICIPANT_STATES = {
    api.ParticipantInfo.State.Value("JOINING"),
    api.ParticipantInfo.State.Value("JOINED"),
    api.ParticipantInfo.State.Value("ACTIVE"),
}


class OutboundCallError(RuntimeError):
    """Raised when an outbound phone call cannot be started cleanly."""


def _is_missing_room_error(error: api.TwirpError) -> bool:
    return str(getattr(error, "code", "") or "").lower() == "not_found" or getattr(error, "status", None) == 404


@dataclass
class CallSettings:
    prompt: str = ""
    language: str = "English"
    gender: str = "Female"
    voice_id: Optional[str] = None
    phone_number: Optional[str] = None
    prospect_id: Optional[str] = None

    @property
    def booking_enabled(self) -> bool:
        return not bool((self.prompt or "").strip())

    @property
    def voice_locale(self) -> str:
        return get_language_locale(self.language)

    @property
    def resolved_voice_id(self) -> str:
        selected_voice = (self.voice_id or "").strip()
        if selected_voice:
            return selected_voice
        return get_default_voice(self.language, self.gender)

    def to_metadata(self) -> dict[str, str]:
        payload = {
            "prompt": (self.prompt or "").strip(),
            "language": self.language,
            "gender": self.gender,
            "voice_id": self.resolved_voice_id,
            "phone_number": self.phone_number or "",
            "prospect_id": self.prospect_id or "",
        }
        return {key: value for key, value in payload.items() if value}

    @classmethod
    def from_metadata(cls, metadata: dict[str, Any]) -> "CallSettings":
        language = str(metadata.get("language", "English") or "English")
        gender = str(metadata.get("gender", "Female") or "Female")
        selected_voice = str(metadata.get("voice_id", "") or "").strip()
        return cls(
            prompt=str(metadata.get("prompt", "") or ""),
            language=language,
            gender=gender,
            voice_id=selected_voice or get_default_voice(language, gender),
            phone_number=str(metadata.get("phone_number")) if metadata.get("phone_number") else None,
            prospect_id=str(metadata.get("prospect_id")) if metadata.get("prospect_id") else None,
        )


def parse_call_metadata(raw_metadata: Any) -> dict[str, Any]:
    if not raw_metadata:
        return {}

    if isinstance(raw_metadata, dict):
        return raw_metadata

    if isinstance(raw_metadata, str):
        try:
            parsed = json.loads(raw_metadata)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        try:
            parsed = ast.literal_eval(raw_metadata)
            if isinstance(parsed, dict):
                return parsed
        except (SyntaxError, ValueError):
            pass

    logger.warning("Unable to parse call metadata, falling back to defaults.")
    return {}


def _format_sip_error(error: api.TwirpError, phone_number: str) -> str:
    sip_status_code = str(error.metadata.get("sip_status_code") or "").strip()
    sip_status = str(error.metadata.get("sip_status") or "").strip()

    if sip_status_code == "480":
        return (
            f"Call to {phone_number} could not be completed because the number is temporarily unavailable "
            "(SIP 480). Try again later, confirm the number is reachable, or use another number."
        )

    if sip_status_code and sip_status:
        return f"Call to {phone_number} could not be completed ({sip_status_code} {sip_status})."

    if sip_status_code:
        return f"Call to {phone_number} could not be completed (SIP {sip_status_code})."

    return f"Call to {phone_number} could not be completed. {getattr(error, 'message', str(error))}"


async def make_call(
    phone_number: str,
    prospect_id: Optional[str] = None,
    call_settings: Optional[CallSettings] = None,
):
    settings = call_settings or CallSettings()

    if not prospect_id:
        prospect = Prospect(phone=phone_number)
        save_prospect_to_db(prospect)
        prospect_id = prospect.id
    elif not get_prospect_from_db(prospect_id):
        save_prospect_to_db(Prospect(id=prospect_id, phone=phone_number))

    settings.phone_number = phone_number
    settings.prospect_id = prospect_id

    lkapi = api.LiveKitAPI(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
        url=LIVEKIT_URL,
    )

    room_name = f"outbound-call-{phone_number.replace('+', '').replace(' ', '')}-{int(asyncio.get_running_loop().time())}"

    try:
        metadata_payload = settings.to_metadata()
        logger.info(
            "Dispatching outbound call with language=%s, gender=%s, voice_id=%s, phone_number=%s, prospect_id=%s",
            settings.language,
            settings.gender,
            metadata_payload.get("voice_id", ""),
            settings.phone_number,
            settings.prospect_id,
        )
        logger.info(f"Creating dispatch for agent {AGENT_NAME} in room {room_name}")
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps(metadata_payload),
            )
        )
        logger.info(f"Created dispatch: {dispatch}")

        if not OUTBOUND_TRUNK_ID or not OUTBOUND_TRUNK_ID.startswith("ST_"):
            raise ValueError("SIP_OUTBOUND_TRUNK_ID is not set or invalid")

        logger.info(f"Dialing {phone_number} to room {room_name}")

        sip_participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=OUTBOUND_TRUNK_ID,
                sip_call_to=phone_number,
                participant_identity=PHONE_PARTICIPANT_IDENTITY,
                wait_until_answered=True,
            )
        )
        logger.info(f"Created SIP participant: {sip_participant}")
        return room_name
    except api.TwirpError as error:
        logger.error(
            "Error creating SIP participant for %s: %s, SIP status: %s %s",
            phone_number,
            getattr(error, "message", str(error)),
            error.metadata.get("sip_status_code") or "unknown",
            error.metadata.get("sip_status") or "unknown",
        )
        raise OutboundCallError(_format_sip_error(error, phone_number)) from error
    except Exception as e:
        logger.error(f"Error making call to {phone_number}: {e}")
        raise
    finally:
        await lkapi.aclose()


async def end_call(room_name: str) -> None:
    cleaned_room_name = (room_name or "").strip()
    if not cleaned_room_name:
        return

    lkapi = api.LiveKitAPI(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
        url=LIVEKIT_URL,
    )

    try:
        logger.info("Ending outbound call in room %s", cleaned_room_name)
        await lkapi.room.delete_room(
            api.DeleteRoomRequest(
                room=cleaned_room_name,
            )
        )
    except api.TwirpError as error:
        if _is_missing_room_error(error):
            logger.info("Room %s was already closed before the end-call request completed.", cleaned_room_name)
            return
        logger.error("Failed to end outbound call in room %s: %s", cleaned_room_name, error.message)
        raise OutboundCallError(f"Could not end call for room {cleaned_room_name}: {error.message}") from error
    finally:
        await lkapi.aclose()


async def is_call_active(room_name: str, participant_identity: str = PHONE_PARTICIPANT_IDENTITY) -> bool:
    cleaned_room_name = (room_name or "").strip()
    if not cleaned_room_name:
        return False

    lkapi = api.LiveKitAPI(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
        url=LIVEKIT_URL,
    )

    try:
        rooms = await lkapi.room.list_rooms(
            api.ListRoomsRequest(
                names=[cleaned_room_name],
            )
        )
        if not list(rooms.rooms):
            return False

        participants = await lkapi.room.list_participants(
            api.ListParticipantsRequest(
                room=cleaned_room_name,
            )
        )
        for participant in participants.participants:
            if participant.identity != participant_identity:
                continue
            return participant.state in ACTIVE_PARTICIPANT_STATES
        return False
    except api.TwirpError as error:
        if _is_missing_room_error(error):
            logger.info("Room %s is no longer active while checking call status.", cleaned_room_name)
            return False
        logger.error("Failed to inspect outbound call state for room %s: %s", cleaned_room_name, error.message)
        raise OutboundCallError(
            f"Could not refresh call status for room {cleaned_room_name}: {error.message}"
        ) from error
    finally:
        await lkapi.aclose()
