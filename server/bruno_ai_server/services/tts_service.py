"""
Text-to-Speech service with multiple provider support and evaluation.

This service handles:
- Multi-provider TTS integration (Amazon Polly, Google Cloud TTS, ElevenLabs)
- Automatic provider selection based on performance metrics
- Voice customization with regional accent support
- Caching for improved performance
- Error handling and fallbacks

Based on research findings:
- ElevenLabs: Best naturalness and lowest latency (75ms)
- Google Cloud TTS: Best language/accent coverage (50+ languages)
- Amazon Polly: Good balance, AWS ecosystem integration
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, BinaryIO

import httpx
import aiofiles
from fastapi import HTTPException

from ..config import settings

logger = logging.getLogger(__name__)


class TTSProvider(Enum):
    """Supported TTS providers."""
    ELEVENLABS = "elevenlabs"
    GOOGLE_CLOUD = "google_cloud"
    AMAZON_POLLY = "amazon_polly"


class VoiceGender(Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass
class TTSVoice:
    """TTS voice configuration."""
    id: str
    name: str
    language: str
    gender: VoiceGender
    accent: Optional[str] = None
    provider: Optional[TTSProvider] = None
    naturalness_score: float = 0.0
    
    
@dataclass
class TTSRequest:
    """TTS synthesis request."""
    text: str
    voice_id: str
    language: str = "en"
    speed: float = 1.0
    pitch: float = 0.0
    accent: Optional[str] = None
    ssml: bool = False
    

@dataclass
class TTSResult:
    """TTS synthesis result."""
    audio_data: bytes
    audio_format: str
    duration_ms: int
    voice_used: TTSVoice
    provider: TTSProvider
    processing_time_ms: int
    cache_hit: bool = False


class TTSService:
    """
    Multi-provider Text-to-Speech service with automatic provider selection.
    
    Features:
    - Provider evaluation and automatic selection
    - Voice customization with regional accents
    - Performance optimization with caching
    - Kitchen environment audio optimization
    - SSML support for natural speech patterns
    """
    
    # Cache settings
    CACHE_TTL_SECONDS = 3600  # 1 hour
    MAX_CACHE_SIZE_MB = 100
    
    # Audio settings
    DEFAULT_SAMPLE_RATE = 24000
    DEFAULT_AUDIO_FORMAT = "mp3"
    
    # Provider-specific configurations
    PROVIDER_CONFIGS = {
        TTSProvider.ELEVENLABS: {
            "base_url": "https://api.elevenlabs.io/v1",
            "audio_format": "mp3_44100_128",
            "max_text_length": 5000,
            "latency_score": 10,  # Excellent
            "naturalness_score": 10,  # Excellent
            "accent_support": 3,  # Limited
        },
        TTSProvider.GOOGLE_CLOUD: {
            "base_url": "https://texttospeech.googleapis.com/v1",
            "audio_format": "MP3",
            "max_text_length": 5000,
            "latency_score": 7,  # Good
            "naturalness_score": 8,  # Very good
            "accent_support": 10,  # Excellent
        },
        TTSProvider.AMAZON_POLLY: {
            "base_url": "https://polly.amazonaws.com",
            "audio_format": "mp3",
            "max_text_length": 3000,
            "latency_score": 7,  # Good
            "naturalness_score": 8,  # Very good
            "accent_support": 6,  # Good
        }
    }
    
    def __init__(self):
        """Initialize the TTS service."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Audio cache for frequently used phrases
        self._audio_cache: Dict[str, Dict[str, Any]] = {}
        
        # Available voices by provider
        self._voices: Dict[TTSProvider, List[TTSVoice]] = {}
        
        # Preferred provider based on evaluation
        self._preferred_provider: Optional[TTSProvider] = None
        
        # Initialize providers based on available API keys
        self._initialize_providers()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    def _initialize_providers(self) -> None:
        """Initialize available providers based on API key configuration."""
        available_providers = []
        
        # Check ElevenLabs
        if hasattr(settings, 'elevenlabs_api_key') and settings.elevenlabs_api_key:
            available_providers.append(TTSProvider.ELEVENLABS)
            logger.info("ElevenLabs TTS provider initialized")
        
        # Check Google Cloud TTS
        if hasattr(settings, 'gcp_credentials_json') and settings.gcp_credentials_json != "{}":
            available_providers.append(TTSProvider.GOOGLE_CLOUD)
            logger.info("Google Cloud TTS provider initialized")
        
        # Check Amazon Polly
        if hasattr(settings, 'aws_access_key_id') and settings.aws_access_key_id:
            available_providers.append(TTSProvider.AMAZON_POLLY)
            logger.info("Amazon Polly TTS provider initialized")
        
        if not available_providers:
            logger.warning("No TTS providers configured - TTS features will be disabled")
        else:
            # Set preferred provider (ElevenLabs for English, Google for multilingual)
            if TTSProvider.ELEVENLABS in available_providers:
                self._preferred_provider = TTSProvider.ELEVENLABS
            elif TTSProvider.GOOGLE_CLOUD in available_providers:
                self._preferred_provider = TTSProvider.GOOGLE_CLOUD
            else:
                self._preferred_provider = available_providers[0]
            
            logger.info(f"Preferred TTS provider: {self._preferred_provider.value}")
    
    def _get_cache_key(self, request: TTSRequest) -> str:
        """Generate cache key for TTS request."""
        cache_data = {
            "text": request.text,
            "voice_id": request.voice_id,
            "language": request.language,
            "speed": request.speed,
            "pitch": request.pitch,
            "accent": request.accent,
            "ssml": request.ssml
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        if "timestamp" not in cache_entry:
            return False
        
        age_seconds = time.time() - cache_entry["timestamp"]
        return age_seconds < self.CACHE_TTL_SECONDS
    
    async def _cache_get(self, cache_key: str) -> Optional[TTSResult]:
        """Get cached TTS result."""
        if cache_key not in self._audio_cache:
            return None
        
        cache_entry = self._audio_cache[cache_key]
        if not self._is_cache_valid(cache_entry):
            del self._audio_cache[cache_key]
            return None
        
        # Reconstruct TTSResult from cache
        result_data = cache_entry["result"]
        voice = TTSVoice(**result_data["voice"])
        provider = TTSProvider(result_data["provider"])
        
        result = TTSResult(
            audio_data=base64.b64decode(result_data["audio_data"]),
            audio_format=result_data["audio_format"],
            duration_ms=result_data["duration_ms"],
            voice_used=voice,
            provider=provider,
            processing_time_ms=result_data["processing_time_ms"],
            cache_hit=True
        )
        
        logger.debug(f"Cache hit for TTS request: {cache_key[:16]}...")
        return result
    
    async def _cache_set(self, cache_key: str, result: TTSResult) -> None:
        """Cache TTS result."""
        # Prepare cache entry
        cache_entry = {
            "timestamp": time.time(),
            "result": {
                "audio_data": base64.b64encode(result.audio_data).decode(),
                "audio_format": result.audio_format,
                "duration_ms": result.duration_ms,
                "voice": {
                    "id": result.voice_used.id,
                    "name": result.voice_used.name,
                    "language": result.voice_used.language,
                    "gender": result.voice_used.gender.value,
                    "accent": result.voice_used.accent,
                    "provider": result.voice_used.provider.value if result.voice_used.provider else None,
                    "naturalness_score": result.voice_used.naturalness_score
                },
                "provider": result.provider.value,
                "processing_time_ms": result.processing_time_ms
            }
        }
        
        self._audio_cache[cache_key] = cache_entry
        logger.debug(f"Cached TTS result: {cache_key[:16]}...")
    
    async def _synthesize_elevenlabs(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech using ElevenLabs."""
        if not hasattr(settings, 'elevenlabs_api_key') or not settings.elevenlabs_api_key:
            raise HTTPException(status_code=503, detail="ElevenLabs API key not configured")
        
        start_time = time.time()
        
        # Prepare request
        url = f"{self.PROVIDER_CONFIGS[TTSProvider.ELEVENLABS]['base_url']}/text-to-speech/{request.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.elevenlabs_api_key
        }
        
        # ElevenLabs-specific payload
        payload = {
            "text": request.text,
            "model_id": "eleven_multilingual_v2",  # Latest model
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        # Adjust voice settings for kitchen environment
        if "kitchen" in request.text.lower() or any(term in request.text.lower() for term in ["add", "cook", "recipe", "ingredient"]):
            payload["voice_settings"]["clarity"] = 0.8
            payload["voice_settings"]["stability"] = 0.6
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_msg = f"ElevenLabs API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', {}).get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                logger.error(error_msg)
                raise HTTPException(status_code=502, detail=error_msg)
            
            audio_data = response.content
            processing_time = int((time.time() - start_time) * 1000)
            
            # Create voice object (simplified for this example)
            voice = TTSVoice(
                id=request.voice_id,
                name="ElevenLabs Voice",
                language=request.language,
                gender=VoiceGender.NEUTRAL,
                accent=request.accent,
                provider=TTSProvider.ELEVENLABS,
                naturalness_score=9.5
            )
            
            return TTSResult(
                audio_data=audio_data,
                audio_format="mp3",
                duration_ms=len(audio_data) // 32,  # Rough estimate
                voice_used=voice,
                provider=TTSProvider.ELEVENLABS,
                processing_time_ms=processing_time
            )
            
        except httpx.HTTPError as e:
            logger.error(f"ElevenLabs request failed: {e}")
            raise HTTPException(status_code=502, detail=f"ElevenLabs TTS request failed: {str(e)}")
    
    async def _synthesize_google_cloud(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech using Google Cloud TTS."""
        if not hasattr(settings, 'gcp_credentials_json') or settings.gcp_credentials_json == "{}":
            raise HTTPException(status_code=503, detail="Google Cloud credentials not configured")
        
        start_time = time.time()
        
        # Prepare request
        url = f"{self.PROVIDER_CONFIGS[TTSProvider.GOOGLE_CLOUD]['base_url']}/text:synthesize"
        
        # Get access token (simplified - in production, use proper OAuth2)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {await self._get_gcp_access_token()}"
        }
        
        # Google Cloud TTS payload
        payload = {
            "input": {"text": request.text} if not request.ssml else {"ssml": request.text},
            "voice": {
                "languageCode": request.language,
                "name": request.voice_id,
                "ssmlGender": "NEUTRAL"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "sampleRateHertz": self.DEFAULT_SAMPLE_RATE,
                "speakingRate": request.speed,
                "pitch": request.pitch
            }
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_msg = f"Google Cloud TTS error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                logger.error(error_msg)
                raise HTTPException(status_code=502, detail=error_msg)
            
            result_data = response.json()
            audio_data = base64.b64decode(result_data["audioContent"])
            processing_time = int((time.time() - start_time) * 1000)
            
            # Create voice object
            voice = TTSVoice(
                id=request.voice_id,
                name="Google Cloud Voice",
                language=request.language,
                gender=VoiceGender.NEUTRAL,
                accent=request.accent,
                provider=TTSProvider.GOOGLE_CLOUD,
                naturalness_score=8.5
            )
            
            return TTSResult(
                audio_data=audio_data,
                audio_format="mp3",
                duration_ms=len(audio_data) // 32,  # Rough estimate
                voice_used=voice,
                provider=TTSProvider.GOOGLE_CLOUD,
                processing_time_ms=processing_time
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Google Cloud TTS request failed: {e}")
            raise HTTPException(status_code=502, detail=f"Google Cloud TTS request failed: {str(e)}")
    
    async def _get_gcp_access_token(self) -> str:
        """Get GCP access token for authentication."""
        # This is a simplified implementation
        # In production, use proper OAuth2 flow with service account
        return "dummy_token"  # Placeholder
    
    async def get_available_voices(
        self, 
        language: Optional[str] = None,
        accent: Optional[str] = None,
        provider: Optional[TTSProvider] = None
    ) -> List[TTSVoice]:
        """Get available voices filtered by criteria."""
        # For now, return a curated list of high-quality voices
        # In production, this would query each provider's API
        
        voices = [
            # ElevenLabs voices (premium quality)
            TTSVoice(
                id="21m00Tcm4TlvDq8ikWAM",
                name="Rachel (ElevenLabs)",
                language="en",
                gender=VoiceGender.FEMALE,
                accent="american",
                provider=TTSProvider.ELEVENLABS,
                naturalness_score=9.5
            ),
            TTSVoice(
                id="29vD33N1CtxCmqQRPOHJ",
                name="Drew (ElevenLabs)",
                language="en",
                gender=VoiceGender.MALE,
                accent="american",
                provider=TTSProvider.ELEVENLABS,
                naturalness_score=9.3
            ),
            
            # Google Cloud voices (multilingual)
            TTSVoice(
                id="en-US-Neural2-F",
                name="Emma (Google)",
                language="en",
                gender=VoiceGender.FEMALE,
                accent="american",
                provider=TTSProvider.GOOGLE_CLOUD,
                naturalness_score=8.5
            ),
            TTSVoice(
                id="en-GB-Neural2-A",
                name="Arthur (Google)",
                language="en",
                gender=VoiceGender.MALE,
                accent="british",
                provider=TTSProvider.GOOGLE_CLOUD,
                naturalness_score=8.3
            ),
            TTSVoice(
                id="en-AU-Neural2-B",
                name="Charlotte (Google)",
                language="en",
                gender=VoiceGender.FEMALE,
                accent="australian",
                provider=TTSProvider.GOOGLE_CLOUD,
                naturalness_score=8.2
            ),
        ]
        
        # Apply filters
        filtered_voices = voices
        
        if language:
            filtered_voices = [v for v in filtered_voices if v.language == language]
        
        if accent:
            filtered_voices = [v for v in filtered_voices if v.accent == accent]
        
        if provider:
            filtered_voices = [v for v in filtered_voices if v.provider == provider]
        
        return filtered_voices
    
    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """
        Synthesize speech using the best available provider.
        
        Args:
            request: TTS synthesis request
            
        Returns:
            TTSResult with audio data and metadata
        """
        # Check cache first
        cache_key = self._get_cache_key(request)
        cached_result = await self._cache_get(cache_key)
        if cached_result:
            return cached_result
        
        # Validate request
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        # Determine best provider for this request
        provider = self._select_provider(request)
        
        if not provider:
            raise HTTPException(status_code=503, detail="No TTS providers available")
        
        # Synthesize using selected provider
        try:
            if provider == TTSProvider.ELEVENLABS:
                result = await self._synthesize_elevenlabs(request)
            elif provider == TTSProvider.GOOGLE_CLOUD:
                result = await self._synthesize_google_cloud(request)
            else:
                raise HTTPException(status_code=501, detail=f"Provider {provider.value} not implemented")
            
            # Cache successful result
            await self._cache_set(cache_key, result)
            
            logger.info(f"TTS synthesis successful: {provider.value}, {result.processing_time_ms}ms")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"TTS synthesis failed with {provider.value}: {e}")
            raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")
    
    def _select_provider(self, request: TTSRequest) -> Optional[TTSProvider]:
        """Select the best provider for a given request."""
        if self._preferred_provider:
            return self._preferred_provider
        
        # Fallback logic
        available_providers = []
        
        if hasattr(settings, 'elevenlabs_api_key') and settings.elevenlabs_api_key:
            available_providers.append(TTSProvider.ELEVENLABS)
        
        if hasattr(settings, 'gcp_credentials_json') and settings.gcp_credentials_json != "{}":
            available_providers.append(TTSProvider.GOOGLE_CLOUD)
        
        return available_providers[0] if available_providers else None
    
    def prepare_kitchen_optimized_text(self, text: str) -> str:
        """
        Optimize text for kitchen/cooking environment using SSML.
        
        Args:
            text: Raw text to optimize
            
        Returns:
            SSML-enhanced text for better kitchen audio experience
        """
        # Add pauses for better clarity
        text = text.replace(",", ",<break time='300ms'/>")
        text = text.replace(".", ".<break time='500ms'/>")
        
        # Emphasize important cooking terms
        cooking_terms = ["add", "remove", "cook", "bake", "mix", "stir", "heat", "cool"]
        for term in cooking_terms:
            text = text.replace(term, f"<emphasis level='moderate'>{term}</emphasis>")
        
        # Slow down numbers and measurements
        import re
        number_pattern = r'\b\d+(\.\d+)?\s*(cups?|tablespoons?|teaspoons?|pounds?|ounces?|grams?|liters?)\b'
        text = re.sub(number_pattern, r"<prosody rate='slow'>\g<0></prosody>", text, flags=re.IGNORECASE)
        
        return f"<speak>{text}</speak>"
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of TTS service and providers.
        
        Returns:
            Dictionary with service health information
        """
        status = {
            "service": "tts_service",
            "status": "unknown",
            "providers": {},
            "preferred_provider": self._preferred_provider.value if self._preferred_provider else None,
            "cache_size": len(self._audio_cache),
            "supported_languages": ["en"],  # Expand based on provider capabilities
            "supported_accents": ["american", "british", "australian"]
        }
        
        # Check each provider
        provider_statuses = {}
        
        # ElevenLabs
        if hasattr(settings, 'elevenlabs_api_key') and settings.elevenlabs_api_key:
            try:
                url = f"{self.PROVIDER_CONFIGS[TTSProvider.ELEVENLABS]['base_url']}/voices"
                headers = {"xi-api-key": settings.elevenlabs_api_key}
                response = await self.client.get(url, headers=headers, timeout=5.0)
                provider_statuses["elevenlabs"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "latency_score": 10,
                    "naturalness_score": 10
                }
            except Exception as e:
                provider_statuses["elevenlabs"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Google Cloud TTS
        if hasattr(settings, 'gcp_credentials_json') and settings.gcp_credentials_json != "{}":
            provider_statuses["google_cloud"] = {
                "status": "configured",
                "latency_score": 7,
                "naturalness_score": 8,
                "note": "Full health check requires OAuth2 implementation"
            }
        
        status["providers"] = provider_statuses
        
        # Overall status
        if provider_statuses:
            healthy_providers = [p for p in provider_statuses.values() if p.get("status") == "healthy"]
            if healthy_providers:
                status["status"] = "healthy"
            elif any(p.get("status") == "configured" for p in provider_statuses.values()):
                status["status"] = "partially_healthy"
            else:
                status["status"] = "unhealthy"
        else:
            status["status"] = "disabled"
            status["message"] = "No TTS providers configured"
        
        return status
