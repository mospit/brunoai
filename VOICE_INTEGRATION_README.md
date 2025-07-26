# Bruno AI Flutter Voice Capture Integration

## Overview

This implementation integrates speech-to-text functionality for local capture, streams to backend STT endpoint, displays real-time transcript, and invokes pantry actions with optimistic UI updates.

## Architecture

### Components

1. **VoiceService** (`client/lib/services/voice_service.dart`)
   - Handles local speech-to-text using the `speech_to_text` package
   - Streams transcribed text to backend for command parsing
   - Provides text-to-speech feedback using `flutter_tts`
   - Manages real-time state and callbacks

2. **VoicePantryScreen** (`client/lib/screens/voice_pantry_screen.dart`)
   - Main UI screen with voice-enabled pantry management
   - Implements optimistic UI updates for immediate feedback
   - Handles voice command results and pantry actions
   - Provides real-time transcript display

3. **Supporting Widgets**
   - **VoiceAnimationWidget**: Animated microphone with sound waves and confidence indicators
   - **TranscriptDisplayWidget**: Real-time transcript display
   - **PantryItemsGridWidget**: Grid display with optimistic update indicators

### Voice Processing Flow

1. **Local Speech Recognition**
   - User taps microphone or says "Hey Bruno"
   - Local STT captures and transcribes speech in real-time
   - Real-time transcript updates shown to user

2. **Command Processing**
   - Final transcript sent to backend `/api/voice/parse-command` endpoint
   - Backend parses commands using AI-powered natural language processing
   - Returns structured pantry actions (add, remove, update, search, etc.)

3. **Optimistic UI Updates**
   - UI immediately reflects expected changes (add/remove items)
   - Background processes handle actual API calls to pantry service
   - Failed operations rollback optimistic changes with error feedback

4. **Voice Feedback**
   - TTS provides audio confirmation of successful actions
   - Natural responses like "Added milk and bread to your pantry"

## Key Features

### Real-time Transcript
- Live speech-to-text display during voice recognition
- Confidence indicators showing recognition quality
- Visual feedback for different voice states (listening, processing, speaking)

### Optimistic UI Updates
- Immediate visual feedback for pantry operations
- Pending operation indicators (orange borders, loading spinners)
- Automatic rollback on server errors
- Maintains consistency between optimistic and actual state

### Voice Commands Supported
- **Add**: "Add 2 cups of milk to the fridge"
- **Remove**: "Remove expired cheese from pantry"
- **Update**: "Update bread quantity to 2 loaves"
- **List**: "What's in my pantry?"
- **Search**: "Search for eggs"
- **Check**: "Check expiration dates"

### Backend Integration
- Connects to FastAPI backend voice processing endpoints
- Handles both local STT + command parsing approach
- Alternative direct audio file upload to backend STT (Voxtral API)
- Proper error handling and retry logic

## Technical Implementation

### Dependencies Added
```yaml
speech_to_text: ^6.3.0      # Local speech recognition
flutter_tts: ^3.8.5         # Text-to-speech feedback
web_socket_channel: ^2.4.0  # Future real-time streaming
uuid: ^4.1.0                # Session ID generation
```

### Key Classes

#### VoiceService
```dart
class VoiceService extends ChangeNotifier {
  // State management
  bool get isListening;
  bool get isProcessing; 
  bool get isSpeaking;
  String get currentTranscript;
  double get confidence;
  
  // Core functionality
  Future<void> startListening();
  Future<void> stopListening();
  Future<void> speak(String text);
  List<PantryItem> convertToPantryItems(List<PantryActionEntity> entities);
}
```

#### Optimistic Updates Pattern
```dart
void _handleAddItems(List<PantryActionEntity> entities) {
  final newItems = _voiceService.convertToPantryItems(entities);
  
  // 1. Optimistic UI update
  setState(() {
    _optimisticItems.addAll(newItems);
  });
  
  // 2. Background API call
  for (final item in newItems) {
    final operationId = '${item.name}_${DateTime.now().millisecondsSinceEpoch}';
    _pendingOperations[operationId] = item;
    _addItemToBackend(item, operationId);
  }
}
```

### Backend API Endpoints

The implementation connects to these backend endpoints:

- `POST /api/voice/parse-command` - Parse text command into structured actions
- `POST /api/voice/process` - Complete audio file processing (alternative)
- `GET /api/voice/health` - Voice service health check

### Permissions

Requires microphone permissions handled through `permission_handler`:
```dart
Future<bool> requestPermissions() async {
  final status = await Permission.microphone.request();
  return status == PermissionStatus.granted;
}
```

## Usage Examples

### Basic Voice Integration
```dart
final voiceService = VoiceService();

// Set up callbacks
voiceService.onTranscriptUpdate = (transcript) {
  print('Real-time: $transcript');
};

voiceService.onCommandProcessed = (result) {
  print('Action: ${result.action}');
  print('Entities: ${result.entities.length}');
};

// Start listening
await voiceService.startListening();
```

### Optimistic UI Pattern
```dart
// Show immediate feedback
setState(() {
  _optimisticItems.add(newItem);
  _pendingOperations[operationId] = newItem;
});

// Handle server response
try {
  final serverItem = await _pantryService.addPantryItem(newItem);
  setState(() {
    // Replace optimistic with server data
    final index = _optimisticItems.indexWhere((i) => /* match condition */);
    _optimisticItems[index] = serverItem;
    _pendingOperations.remove(operationId);
  });
} catch (e) {
  // Rollback on error
  setState(() {
    _optimisticItems.removeWhere((i) => /* match condition */);
    _pendingOperations.remove(operationId);
  });
}
```

## Configuration

### Voice Service Settings
- Language: 'en_US' (configurable per user)
- Listen duration: 30 seconds max
- Pause detection: 3 seconds
- TTS settings: Rate 0.9, Volume 0.8, Pitch 1.0

### Backend Integration
- Base URL: 'http://localhost:8000/api' (configurable)
- Request timeout: 10 seconds for commands, 30 seconds for audio
- Retry logic: Automatic rollback on failures

## Error Handling

1. **Microphone Permission Denied**: Shows error message with instructions
2. **Speech Recognition Unavailable**: Fallback to text input
3. **Network Errors**: Optimistic rollback with error notification
4. **Command Parsing Failures**: TTS feedback requesting clarification
5. **Backend Service Down**: Graceful degradation with local-only mode

## Performance Considerations

- Real-time transcript updates use `ChangeNotifier` for efficient UI updates
- Optimistic operations minimize perceived latency
- Audio processing is handled asynchronously to prevent UI blocking
- Background API calls use proper timeout and error handling

## Future Enhancements

1. **WebSocket Streaming**: Real-time audio streaming to backend
2. **Voice Command Shortcuts**: "Hey Bruno" wake word activation
3. **Multi-language Support**: Dynamic language switching
4. **Offline Mode**: Local command processing when backend unavailable
5. **Voice Training**: User-specific voice pattern learning

## Testing

The implementation includes:
- Unit tests for voice service functionality
- Integration tests for voice-to-pantry workflows
- Mock services for offline development
- Error simulation for resilience testing

## Deployment Notes

1. **Mobile Permissions**: Ensure microphone permissions in Android/iOS manifests
2. **Backend Connectivity**: Configure proper API endpoints for production
3. **Voice API Keys**: Set up Voxtral API credentials for server-side STT
4. **Network Requirements**: Voice features require stable internet connection

This implementation provides a complete voice-enabled pantry management experience with real-time feedback, optimistic updates, and robust error handling.
