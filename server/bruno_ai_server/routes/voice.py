"""
Voice processing API routes for Bruno AI Server.

Provides endpoints for:
- Audio transcription using Mistral Voxtral STT
- Voice command parsing and pantry action extraction
- Combined voice-to-action processing
- Voice service health checks
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse

from ..auth import get_current_user
from ..models.user import User
from ..services.voice_service import VoiceService, TranscriptionResult
from ..services.command_parser import CommandParser, CommandResult
from ..services.tts_service import TTSService, TTSRequest, TTSProvider
from ..schemas import (
    VoiceTranscriptionRequest,
    VoiceTranscriptionResponse,
    PantryActionEntity,
    PantryActionCommand,
    VoiceCommandResponse,
    TTSSynthesisRequest,
    TTSSynthesisResponse,
    TTSVoiceResponse,
    TTSHealthResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Language hint (e.g., 'en', 'es', 'fr')"),
    enhance_food_terms: bool = Form(True, description="Whether to optimize for food term recognition"),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio file to text using Mistral Voxtral STT.
    
    This endpoint accepts raw audio files and returns transcribed text
    optimized for food-related vocabulary with 95%+ accuracy target.
    
    Supported formats: WAV, MP3, M4A, OGG, WebM, FLAC
    Maximum file size: 50MB
    Maximum duration: 5 minutes
    """
    try:
        async with VoiceService() as voice_service:
            # Transcribe the audio
            result = await voice_service.transcribe_audio(
                file=audio_file,
                language=language,
                enhance_food_terms=enhance_food_terms
            )
            
            logger.info(f"Transcription completed for user {current_user.id}: '{result.text[:100]}...'")
            
            return VoiceTranscriptionResponse(
                text=result.text,
                confidence=result.confidence,
                language_detected=result.language_detected,
                processing_time_ms=result.processing_time_ms,
                audio_duration_ms=result.audio_duration_ms
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio transcription failed: {str(e)}"
        )


@router.post("/parse-command", response_model=PantryActionCommand)
async def parse_voice_command(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """
    Parse voice command text and extract structured pantry actions.
    
    This endpoint takes transcribed text and identifies:
    - Action type (add, update, delete, list, search, check)
    - Food entities with quantities, units, locations, expiration dates
    - Command confidence and validation
    
    Example commands:
    - "Add 2 pounds of chicken to the fridge"
    - "Remove expired milk"
    - "What's in my pantry?"
    - "Update bread quantity to 2 loaves"
    """
    try:
        parser = CommandParser()
        result = parser.parse_command(text)
        
        # Convert to response schema
        entities = [
            PantryActionEntity(
                name=entity.name,
                quantity=entity.quantity,
                unit=entity.unit,
                location=entity.location,
                expiration_date=entity.expiration_date,
                confidence=entity.confidence
            )
            for entity in result.entities
        ]
        
        logger.info(f"Command parsed for user {current_user.id}: {result.action.value} with {len(entities)} entities")
        
        return PantryActionCommand(
            action=result.action.value,
            entities=entities,
            raw_text=result.raw_text,
            confidence=result.confidence,
            errors=result.errors,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Command parsing failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Command parsing failed: {str(e)}"
        )


@router.post("/process", response_model=VoiceCommandResponse)
async def process_voice_command(
    audio_file: UploadFile = File(..., description="Audio file containing voice command"),
    language: Optional[str] = Form(None, description="Language hint for transcription"),
    enhance_food_terms: bool = Form(True, description="Optimize transcription for food terms"),
    current_user: User = Depends(get_current_user)
):
    """
    Complete voice-to-action processing pipeline.
    
    This endpoint combines audio transcription and command parsing into a single
    operation, providing end-to-end voice command processing.
    
    Steps:
    1. Transcribe audio using Mistral Voxtral STT
    2. Parse transcribed text for pantry actions
    3. Return structured command with entities
    
    This is the primary endpoint for voice-enabled pantry management.
    """
    try:
        async with VoiceService() as voice_service:
            # Step 1: Transcribe audio
            transcription = await voice_service.transcribe_audio(
                file=audio_file,
                language=language,
                enhance_food_terms=enhance_food_terms
            )
            
            logger.info(f"Voice processing step 1/2 complete for user {current_user.id}: transcription")
            
            # Step 2: Parse command
            parser = CommandParser()
            command_result = parser.parse_command(transcription.text)
            
            # Validate command result
            is_valid = parser.validate_command_result(command_result)
            
            # Convert to response schemas
            transcription_response = VoiceTranscriptionResponse(
                text=transcription.text,
                confidence=transcription.confidence,
                language_detected=transcription.language_detected,
                processing_time_ms=transcription.processing_time_ms,
                audio_duration_ms=transcription.audio_duration_ms
            )
            
            entities = [
                PantryActionEntity(
                    name=entity.name,
                    quantity=entity.quantity,
                    unit=entity.unit,
                    location=entity.location,
                    expiration_date=entity.expiration_date,
                    confidence=entity.confidence
                )
                for entity in command_result.entities
            ]
            
            command_response = PantryActionCommand(
                action=command_result.action.value,
                entities=entities,
                raw_text=command_result.raw_text,
                confidence=command_result.confidence,
                errors=command_result.errors,
                metadata=command_result.metadata
            )
            
            # Determine success and message
            success = is_valid and transcription.confidence > 0.7 and command_result.confidence > 0.5
            message = None
            
            if not success:
                if transcription.confidence <= 0.7:
                    message = "Low confidence in audio transcription. Please try speaking more clearly."
                elif command_result.confidence <= 0.5:
                    message = "Unable to understand command. Please try rephrasing."
                elif not is_valid:
                    message = "Command could not be validated for execution."
            
            logger.info(f"Voice processing complete for user {current_user.id}: success={success}")
            
            return VoiceCommandResponse(
                transcription=transcription_response,
                command=command_response,
                success=success,
                message=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice command processing failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice command processing failed: {str(e)}"
        )


@router.get("/health")
async def voice_service_health():
    """
    Check the health status of voice processing services.
    
    Returns status information for:
    - Mistral Voxtral STT API connectivity
    - Voice service configuration
    - Supported audio formats and limits
    """
    try:
        async with VoiceService() as voice_service:
            health_status = await voice_service.health_check()
            
            # Add command parser status
            parser = CommandParser()
            health_status["command_parser"] = {
                "status": "healthy",
                "supported_actions": parser.get_supported_actions()
            }
            
            return health_status
            
    except Exception as e:
        logger.error(f"Voice service health check failed: {e}")
        return {
            "service": "voice_service",
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get information about supported audio formats and processing limits.
    
    Returns:
    - Supported audio file formats
    - Maximum file size and duration limits
    - Recommended settings for optimal recognition
    """
    return {
        "supported_formats": list(VoiceService.SUPPORTED_FORMATS),
        "max_file_size_mb": VoiceService.MAX_FILE_SIZE // (1024 * 1024),
        "max_duration_seconds": VoiceService.MAX_DURATION_SECONDS,
        "recommended_settings": {
            "sample_rate": "16kHz or higher",
            "bit_depth": "16-bit minimum",
            "channels": "mono or stereo",
            "format": "WAV or MP3 preferred",
            "environment": "minimize background noise for best results"
        },
        "optimization_notes": [
            "Speech-to-text is optimized for food and kitchen vocabulary",
            "Works best with clear pronunciation of food items and quantities",
            "Supports common cooking measurements and terms",
            "Can handle kitchen background noise to some extent"
        ]
    }


# TTS endpoints for text-to-speech functionality
@router.post("/speak", response_model=TTSSynthesisResponse)
async def synthesize_speech(
    request: TTSSynthesisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Convert text to speech using the best available TTS provider.
    
    This endpoint accepts text and returns synthesized audio optimized for
    kitchen environments and family-friendly interactions.
    
    Supported providers: ElevenLabs, Google Cloud TTS, Amazon Polly
    Regional accents: American, British, Australian
    
    Features:
    - Automatic provider selection based on naturalness and latency
    - Kitchen environment optimization with SSML
    - Caching for frequently used phrases
    - Regional accent selection
    """
    try:
        async with TTSService() as tts_service:
            # Get available voices to validate voice_id
            if request.voice_id:
                available_voices = await tts_service.get_available_voices(
                    language=request.language,
                    accent=request.accent
                )
                voice_ids = [v.id for v in available_voices]
                if request.voice_id not in voice_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Voice ID '{request.voice_id}' not available. Available voices: {voice_ids}"
                    )
            else:
                # Auto-select best voice based on criteria
                available_voices = await tts_service.get_available_voices(
                    language=request.language,
                    accent=request.accent
                )
                if not available_voices:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No voices available for language '{request.language}' and accent '{request.accent}'"
                    )
                # Select highest naturalness score
                best_voice = max(available_voices, key=lambda v: v.naturalness_score)
                request.voice_id = best_voice.id
            
            # Optimize text for kitchen environment if requested
            text = request.text
            if request.optimize_for_kitchen:
                text = tts_service.prepare_kitchen_optimized_text(text)
                request.ssml = True
            
            # Create TTS request
            tts_request = TTSRequest(
                text=text,
                voice_id=request.voice_id,
                language=request.language,
                speed=request.speed,
                pitch=request.pitch,
                accent=request.accent,
                ssml=request.ssml
            )
            
            # Synthesize speech
            result = await tts_service.synthesize(tts_request)
            
            # Convert result to response schema
            import base64
            
            voice_response = TTSVoiceResponse(
                id=result.voice_used.id,
                name=result.voice_used.name,
                language=result.voice_used.language,
                gender=result.voice_used.gender.value,
                accent=result.voice_used.accent,
                provider=result.voice_used.provider.value if result.voice_used.provider else None,
                naturalness_score=result.voice_used.naturalness_score
            )
            
            logger.info(f"TTS synthesis completed for user {current_user.id}: {result.provider.value}, {result.processing_time_ms}ms")
            
            return TTSSynthesisResponse(
                audio_data=base64.b64encode(result.audio_data).decode(),
                audio_format=result.audio_format,
                duration_ms=result.duration_ms,
                voice_used=voice_response,
                provider=result.provider.value,
                processing_time_ms=result.processing_time_ms,
                cache_hit=result.cache_hit
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS synthesis failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS synthesis failed: {str(e)}"
        )


@router.get("/voices", response_model=List[TTSVoiceResponse])
async def get_available_voices(
    language: Optional[str] = None,
    accent: Optional[str] = None,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get available TTS voices filtered by criteria.
    
    Returns a list of available voices that can be used with the /speak endpoint.
    Voices are sorted by naturalness score (highest first).
    
    Query parameters:
    - language: Filter by language code (e.g., 'en', 'es', 'fr')
    - accent: Filter by accent (e.g., 'american', 'british', 'australian')
    - provider: Filter by provider ('elevenlabs', 'google_cloud', 'amazon_polly')
    """
    try:
        async with TTSService() as tts_service:
            # Convert provider string to enum if provided
            provider_enum = None
            if provider:
                try:
                    provider_enum = TTSProvider(provider)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid provider '{provider}'. Valid providers: {[p.value for p in TTSProvider]}"
                    )
            
            # Get available voices
            voices = await tts_service.get_available_voices(
                language=language,
                accent=accent,
                provider=provider_enum
            )
            
            # Convert to response schema and sort by naturalness
            voice_responses = [
                TTSVoiceResponse(
                    id=voice.id,
                    name=voice.name,
                    language=voice.language,
                    gender=voice.gender.value,
                    accent=voice.accent,
                    provider=voice.provider.value if voice.provider else None,
                    naturalness_score=voice.naturalness_score
                )
                for voice in voices
            ]
            
            # Sort by naturalness score (highest first)
            voice_responses.sort(key=lambda v: v.naturalness_score, reverse=True)
            
            logger.info(f"Retrieved {len(voice_responses)} voices for user {current_user.id}")
            return voice_responses
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voices for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve voices: {str(e)}"
        )


@router.get("/tts-health", response_model=TTSHealthResponse)
async def tts_service_health():
    """
    Check the health status of TTS services and providers.
    
    Returns detailed status information for each configured TTS provider,
    including latency scores, naturalness ratings, and configuration status.
    
    Useful for monitoring TTS service availability and selecting optimal providers.
    """
    try:
        async with TTSService() as tts_service:
            health_status = await tts_service.health_check()
            
            # Convert to response schema
            from ..schemas import TTSProviderStatus
            
            providers = {}
            for provider_name, status_data in health_status["providers"].items():
                providers[provider_name] = TTSProviderStatus(
                    status=status_data["status"],
                    latency_score=status_data.get("latency_score"),
                    naturalness_score=status_data.get("naturalness_score"),
                    error=status_data.get("error"),
                    note=status_data.get("note")
                )
            
            return TTSHealthResponse(
                service=health_status["service"],
                status=health_status["status"],
                providers=providers,
                preferred_provider=health_status["preferred_provider"],
                cache_size=health_status["cache_size"],
                supported_languages=health_status["supported_languages"],
                supported_accents=health_status["supported_accents"],
                message=health_status.get("message")
            )
            
    except Exception as e:
        logger.error(f"TTS service health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS health check failed: {str(e)}"
        )


# Streaming endpoint (future implementation)
@router.post("/stream")
async def process_streaming_audio(
    current_user: User = Depends(get_current_user)
):
    """
    Process streaming audio for real-time voice commands.
    
    This endpoint is reserved for future implementation of real-time
    audio streaming and processing capabilities.
    
    Currently returns a not implemented error.
    """
    raise HTTPException(
        status_code=501,
        detail="Streaming audio processing not yet implemented. Use /process endpoint for file-based processing."
    )
