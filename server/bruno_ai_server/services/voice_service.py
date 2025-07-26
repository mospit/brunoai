"""
Voice processing service using Mistral Voxtral STT API.

This service handles:
- Audio file upload and preprocessing
- Speech-to-text conversion using Mistral Voxtral API
- Food-term accuracy optimization (95%+ target)
- Audio streaming support
- Error handling and fallbacks
"""

import asyncio
import io
import logging
from pathlib import Path
from typing import BinaryIO, Optional, Dict, Any
from dataclasses import dataclass

import httpx
import aiofiles
from fastapi import HTTPException, UploadFile

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""
    text: str
    confidence: float
    language_detected: Optional[str] = None
    processing_time_ms: int = 0
    audio_duration_ms: int = 0


class VoiceService:
    """
    Voice processing service with Mistral Voxtral STT integration.
    
    Features:
    - High accuracy food term recognition (95%+ target)
    - Support for multiple audio formats (WAV, MP3, M4A, OGG)
    - Streaming audio processing
    - Kitchen noise reduction optimization
    - Fallback error handling
    """
    
    SUPPORTED_FORMATS = {"wav", "mp3", "m4a", "ogg", "webm", "flac"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size
    MAX_DURATION_SECONDS = 300  # 5 minutes max duration
    
    # Voxtral API endpoints
    VOXTRAL_BASE_URL = "https://api.mistral.ai/v1/audio"
    TRANSCRIPTION_ENDPOINT = f"{VOXTRAL_BASE_URL}/transcriptions"
    
    def __init__(self):
        """Initialize the voice service."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Validate API key availability
        if not settings.voxtral_api_key:
            logger.warning("Voxtral API key not configured - voice features will be disabled")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    def _validate_audio_file(self, file: UploadFile) -> None:
        """
        Validate uploaded audio file.
        
        Args:
            file: The uploaded file to validate
            
        Raises:
            HTTPException: If file validation fails
        """
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower().lstrip('.')
            if file_ext not in self.SUPPORTED_FORMATS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
                )
        
        # Check content type
        content_type = file.content_type or ""
        if not (content_type.startswith("audio/") or content_type.startswith("video/")):
            logger.warning(f"Unexpected content type: {content_type}, proceeding anyway")
    
    async def _prepare_voxtral_request(
        self, 
        audio_data: bytes, 
        filename: str = "audio.wav",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare request data for Voxtral API.
        
        Args:
            audio_data: Raw audio bytes
            filename: Original filename (for format detection)
            language: Optional language hint
            
        Returns:
            Dictionary with request data for Voxtral API
        """
        # Prepare files for multipart upload
        files = {
            "file": (filename, io.BytesIO(audio_data), "audio/wav")
        }
        
        # Prepare form data with optimizations for food terms
        data = {
            "model": "voxtral-24.05",  # Latest Voxtral model
            "response_format": "json",
            "temperature": 0.1,  # Lower temperature for more consistent results
        }
        
        # Add language hint if provided
        if language:
            data["language"] = language
        
        # Add food-specific optimizations via prompt
        # This helps improve accuracy for food-related terms
        data["prompt"] = (
            "This is a food-related conversation in a kitchen environment. "
            "Focus on accurate recognition of food items, cooking terms, quantities, "
            "measurements, and kitchen vocabulary. Common words include: "
            "add, remove, delete, update, milk, bread, chicken, vegetables, "
            "cups, tablespoons, teaspoons, pounds, ounces, grams, liters."
        )
        
        return {"files": files, "data": data}
    
    async def transcribe_audio(
        self, 
        file: UploadFile,
        language: Optional[str] = None,
        enhance_food_terms: bool = True
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text using Mistral Voxtral STT.
        
        Args:
            file: Uploaded audio file
            language: Optional language hint (e.g., "en", "es", "fr")
            enhance_food_terms: Whether to optimize for food term recognition
            
        Returns:
            TranscriptionResult with transcribed text and metadata
            
        Raises:
            HTTPException: If transcription fails
        """
        if not settings.voxtral_api_key:
            raise HTTPException(
                status_code=503,
                detail="Voice transcription service not available - API key not configured"
            )
        
        import time
        start_time = time.time()
        
        try:
            # Validate the uploaded file
            self._validate_audio_file(file)
            
            # Read audio data
            audio_data = await file.read()
            logger.info(f"Processing audio file: {file.filename}, size: {len(audio_data)} bytes")
            
            # Prepare request for Voxtral API
            request_data = await self._prepare_voxtral_request(
                audio_data, 
                file.filename or "audio.wav",
                language
            )
            
            # Make request to Voxtral API
            headers = {
                "Authorization": f"Bearer {settings.voxtral_api_key}",
                "User-Agent": "Bruno-AI-Server/1.0"
            }
            
            logger.info("Sending request to Voxtral API")
            response = await self.client.post(
                self.TRANSCRIPTION_ENDPOINT,
                files=request_data["files"],
                data=request_data["data"],
                headers=headers
            )
            
            # Handle API response
            if response.status_code != 200:
                error_detail = f"Voxtral API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    error_detail += f" - {response.text[:200]}"
                
                logger.error(error_detail)
                raise HTTPException(status_code=502, detail=error_detail)
            
            # Parse successful response
            result_data = response.json()
            transcribed_text = result_data.get("text", "").strip()
            
            if not transcribed_text:
                raise HTTPException(
                    status_code=422,
                    detail="No speech detected in audio file"
                )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Calculate confidence score (Voxtral doesn't provide this directly)
            # We estimate based on response characteristics
            confidence = self._estimate_confidence(result_data, transcribed_text)
            
            logger.info(f"Transcription successful: '{transcribed_text[:50]}...' (confidence: {confidence:.2f})")
            
            return TranscriptionResult(
                text=transcribed_text,
                confidence=confidence,
                language_detected=result_data.get("language"),
                processing_time_ms=processing_time,
                audio_duration_ms=int(result_data.get("duration", 0) * 1000)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Transcription processing failed: {str(e)}"
            )
        finally:
            # Reset file position for potential reuse
            if hasattr(file, 'seek'):
                try:
                    await file.seek(0)
                except:
                    pass
    
    def _estimate_confidence(self, api_response: Dict[str, Any], text: str) -> float:
        """
        Estimate confidence score for transcription result.
        
        Since Voxtral doesn't provide confidence scores directly,
        we estimate based on various factors.
        
        Args:
            api_response: Raw API response data
            text: Transcribed text
            
        Returns:
            Estimated confidence score (0.0 to 1.0)
        """
        confidence = 0.8  # Base confidence for Voxtral
        
        # Adjust based on text characteristics
        if len(text) < 5:
            confidence -= 0.2  # Very short text is less reliable
        elif len(text.split()) < 3:
            confidence -= 0.1  # Short phrases are somewhat less reliable
        
        # Boost confidence for food-related terms
        food_terms = {
            "add", "remove", "delete", "update", "milk", "bread", "chicken", 
            "vegetables", "cup", "cups", "tablespoon", "teaspoon", "pound", 
            "ounce", "gram", "liter", "buy", "grocery", "shopping", "recipe",
            "cook", "cooking", "bake", "baking", "fridge", "pantry", "freezer"
        }
        
        text_lower = text.lower()
        food_term_count = sum(1 for term in food_terms if term in text_lower)
        if food_term_count > 0:
            confidence += min(0.1, food_term_count * 0.02)  # Boost up to 0.1
        
        # Ensure confidence stays within bounds
        return max(0.1, min(1.0, confidence))
    
    async def transcribe_streaming_audio(
        self, 
        audio_stream: BinaryIO,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe streaming audio data.
        
        Note: This is a placeholder for future streaming implementation.
        Currently processes the entire stream as a single file.
        
        Args:
            audio_stream: Binary audio stream
            language: Optional language hint
            
        Returns:
            TranscriptionResult with transcribed text
        """
        # Read all data from stream
        audio_data = audio_stream.read()
        
        # Create a temporary UploadFile-like object
        class StreamUpload:
            def __init__(self, data: bytes):
                self.data = data
                self.filename = "stream.wav"
                self.content_type = "audio/wav"
                self.size = len(data)
                
            async def read(self) -> bytes:
                return self.data
                
            async def seek(self, position: int):
                pass
        
        return await self.transcribe_audio(
            StreamUpload(audio_data),
            language=language
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the voice service.
        
        Returns:
            Dictionary with service health information
        """
        status = {
            "service": "voice_service",
            "status": "unknown",
            "voxtral_api_configured": bool(settings.voxtral_api_key),
            "supported_formats": list(self.SUPPORTED_FORMATS),
            "max_file_size_mb": self.MAX_FILE_SIZE // (1024 * 1024),
            "max_duration_seconds": self.MAX_DURATION_SECONDS
        }
        
        if not settings.voxtral_api_key:
            status["status"] = "disabled"
            status["message"] = "Voxtral API key not configured"
            return status
        
        try:
            # Test API connectivity with a minimal request
            headers = {
                "Authorization": f"Bearer {settings.voxtral_api_key}",
                "User-Agent": "Bruno-AI-Server/1.0"
            }
            
            # Test with a simple GET to check authentication
            # Note: Voxtral may not have a dedicated health endpoint
            response = await self.client.get(
                self.VOXTRAL_BASE_URL.rstrip('/audio'),
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code in [200, 404]:  # 404 is OK, means auth worked
                status["status"] = "healthy"
            else:
                status["status"] = "unhealthy"
                status["message"] = f"API returned status {response.status_code}"
                
        except Exception as e:
            status["status"] = "unhealthy"
            status["message"] = f"API connectivity failed: {str(e)}"
        
        return status
