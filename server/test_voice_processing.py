"""
Test script for voice processing functionality.

This script demonstrates and tests the voice processing pipeline:
1. Command parsing without audio (for testing)
2. Voice service health checks
3. Example command processing

To run with audio:
1. Set up your Voxtral API key in .env file
2. Run the server: python main.py
3. Use the /api/voice endpoints via HTTP requests
"""

import asyncio
import sys
from pathlib import Path

# Add the server package to the path
sys.path.append(str(Path(__file__).parent))

from bruno_ai_server.services.command_parser import CommandParser
from bruno_ai_server.services.voice_service import VoiceService
from bruno_ai_server.config import settings


async def test_command_parser():
    """Test the command parser with various example commands."""
    parser = CommandParser()
    
    test_commands = [
        "Add 2 pounds of chicken to the fridge",
        "I bought milk and bread",
        "Remove expired yogurt",
        "What's in my pantry?",
        "Update milk quantity to 1 gallon",
        "Delete old cheese",
        "Put the bananas in the pantry",
        "I have 3 cans of tomatoes",
        "Check when does the milk expire",
        "Find eggs in the fridge",
    ]
    
    print("=" * 60)
    print("TESTING COMMAND PARSER")
    print("=" * 60)
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}. Testing: '{command}'")
        result = parser.parse_command(command)
        
        print(f"   Action: {result.action.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Valid: {parser.validate_command_result(result)}")
        
        if result.entities:
            print(f"   Entities ({len(result.entities)}):")
            for entity in result.entities:
                parts = [f"name='{entity.name}'"]
                if entity.quantity:
                    parts.append(f"qty={entity.quantity}")
                if entity.unit:
                    parts.append(f"unit='{entity.unit}'")
                if entity.location:
                    parts.append(f"loc='{entity.location}'")
                if entity.expiration_date:
                    parts.append(f"exp='{entity.expiration_date}'")
                print(f"     - {', '.join(parts)} (conf: {entity.confidence:.2f})")
        else:
            print("   No entities found")
        
        if result.errors:
            print(f"   Errors: {result.errors}")


async def test_voice_service_health():
    """Test the voice service health check."""
    print("\n" + "=" * 60)
    print("TESTING VOICE SERVICE HEALTH")
    print("=" * 60)
    
    try:
        async with VoiceService() as voice_service:
            health = await voice_service.health_check()
            
            print(f"Service: {health['service']}")
            print(f"Status: {health['status']}")
            print(f"Voxtral API Configured: {health['voxtral_api_configured']}")
            print(f"Supported Formats: {', '.join(health['supported_formats'])}")
            print(f"Max File Size: {health['max_file_size_mb']}MB")
            print(f"Max Duration: {health['max_duration_seconds']}s")
            
            if 'message' in health:
                print(f"Message: {health['message']}")
                
    except Exception as e:
        print(f"Voice service health check failed: {e}")


def test_supported_actions():
    """Test supported actions listing."""
    print("\n" + "=" * 60)
    print("SUPPORTED ACTIONS")
    print("=" * 60)
    
    parser = CommandParser()
    actions = parser.get_supported_actions()
    print(f"Supported actions: {', '.join(actions)}")


async def demonstrate_voice_pipeline():
    """Demonstrate the complete voice processing pipeline."""
    print("\n" + "=" * 60)
    print("VOICE PROCESSING PIPELINE DEMONSTRATION")
    print("=" * 60)
    
    # This would be the flow for actual audio processing:
    print("""
Complete Voice Processing Flow:
1. User records audio (mobile app)
2. Audio uploaded to /api/voice/process endpoint
3. Server transcribes audio using Mistral Voxtral STT
4. Server parses transcribed text for pantry actions
5. Server returns structured command with entities
6. Mobile app executes pantry actions based on response

Example API calls:
- POST /api/voice/transcribe (audio file → text)
- POST /api/voice/parse-command (text → structured command)  
- POST /api/voice/process (audio file → complete processing)
- GET /api/voice/health (service status check)
- GET /api/voice/supported-formats (format information)
""")
    
    print("\nConfiguration Status:")
    print(f"- Voxtral API Key: {'✓ Configured' if settings.voxtral_api_key else '✗ Not configured'}")
    print(f"- Environment: {settings.environment}")
    print(f"- Debug Mode: {settings.debug}")


async def main():
    """Run all tests."""
    print("Bruno AI Voice Processing Test Suite")
    
    await test_command_parser()
    await test_voice_service_health()
    test_supported_actions()
    await demonstrate_voice_pipeline()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("""
To test with actual audio:
1. Set VOXTRAL_API_KEY in your .env file
2. Start the server: python main.py
3. Use curl or a REST client to test endpoints:

   # Test transcription
   curl -X POST "http://localhost:8000/api/voice/transcribe" \\
        -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
        -F "audio_file=@test_audio.wav"
   
   # Test complete processing
   curl -X POST "http://localhost:8000/api/voice/process" \\
        -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
        -F "audio_file=@test_audio.wav"
""")


if __name__ == "__main__":
    asyncio.run(main())
