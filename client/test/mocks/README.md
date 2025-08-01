# Bruno AI Client Test Mocks

This directory contains comprehensive mock definitions and utilities for testing the Bruno AI client application.

## Overview

The mock system provides complete test doubles for all external dependencies and internal services, enabling reliable unit and integration testing without dependencies on real network services, databases, or platform APIs.

## Generated Mock Files

The following files are automatically generated by `build_runner` and should not be edited manually:

- `all_mocks.mocks.dart` - Contains all mock classes
- `connectivity_mocks.mocks.dart` - Connectivity-specific mocks
- `database_mocks.mocks.dart` - Database-specific mocks
- `pantry_service_mocks.mocks.dart` - Pantry service mocks
- `voice_service_mocks.mocks.dart` - Voice service mocks

## Mock Definitions

### External Dependencies
- **MockConnectivity** - Mock for connectivity_plus package
- **MockClient** - Mock for HTTP client operations
- **MockDatabase** - Mock for SQLite database operations
- **MockBatch** - Mock for database batch operations  
- **MockTransaction** - Mock for database transactions
- **MockSpeechToText** - Mock for speech recognition
- **MockFlutterTts** - Mock for text-to-speech

### Internal Services
- **MockPantryService** - Mock for pantry API operations
- **MockCategoryService** - Mock for category management
- **MockOfflineStorageService** - Mock for local storage
- **MockSyncService** - Mock for data synchronization
- **MockVoiceService** - Mock for voice processing
- **MockProductLookupService** - Mock for barcode lookups

## Usage

### Basic Setup

```dart
import 'package:flutter_test/flutter_test.dart';
import '../mocks/mocks.dart';

void main() {
  group('MyService Tests', () {
    late MockPantryService mockPantryService;
    late MockConnectivity mockConnectivity;

    setUp(() {
      mockPantryService = MockPantryService();
      mockConnectivity = MockConnectivity();
    });

    test('should work with mocks', () async {
      // Setup mock behavior
      final sampleItems = TestUtilities.createSamplePantryItems();
      TestUtilities.setupMockPantryService(mockPantryService, sampleItems);
      
      // Test your code here
    });
  });
}
```

### Test Utilities

The `TestUtilities` class provides convenient helper methods:

#### Mock Setup Helpers
- `setupMockConnectivity()` - Configure connectivity mocks
- `setupMockHttpSuccess()` - Setup successful HTTP responses
- `setupMockHttpError()` - Setup HTTP error responses
- `setupMockPantryService()` - Setup pantry service mocks
- `setupMockCategoryService()` - Setup category service mocks
- `setupMockOfflineStorage()` - Setup offline storage mocks

#### Sample Data Creators
- `createSamplePantryItem()` - Create test pantry items
- `createSampleCategory()` - Create test categories
- `createSampleProduct()` - Create test products
- `createSamplePantryItems()` - Create lists of test items
- `createSampleCategories()` - Create lists of test categories

#### Test Helpers
- `createMockHttpResponse()` - Create HTTP response objects
- `verifyMockCall()` - Verify mock method calls
- `resetMocks()` - Reset mocks between tests

### Test Constants

The `TestConstants` class provides common test values:

- `mockBaseUrl` - Test API base URL
- `validBarcode` - Valid test barcode
- `invalidBarcode` - Invalid test barcode
- `mockHeaders` - Standard HTTP headers
- `mockPantryItemJson` - Sample JSON responses
- `mockCategoryJson` - Sample category JSON
- `mockProductJson` - Sample product JSON

## Regenerating Mocks

When you add new services or modify existing ones, regenerate the mocks:

```bash
dart run build_runner build --delete-conflicting-outputs
```

## Mock Categories

### Network & Connectivity
- Connectivity status checking
- HTTP client operations
- Network request/response handling

### Database & Storage
- SQLite database operations
- Local data persistence
- Batch operations and transactions

### Voice & Audio  
- Speech-to-text recognition
- Text-to-speech synthesis
- Audio permission handling

### Pantry Management
- CRUD operations for pantry items
- Category management
- Product lookups via barcode

### Data Synchronization
- Online/offline data sync
- Conflict resolution
- Background sync operations

## Best Practices

### 1. Use TestUtilities
Always use the provided utility methods instead of setting up mocks manually:

```dart
// Good
TestUtilities.setupMockPantryService(mockService, items);

// Avoid
when(mockService.getPantryItems()).thenAnswer((_) async => items);
```

### 2. Reset Mocks Between Tests
Use the reset utility in tearDown:

```dart
tearDown(() {
  TestUtilities.resetMocks([mockService1, mockService2]);
});
```

### 3. Use Sample Data Creators
Generate consistent test data:

```dart
final items = TestUtilities.createSamplePantryItems(count: 5);
final categories = TestUtilities.createSampleCategories(count: 3);
```

### 4. Verify Mock Interactions
Always verify important mock calls:

```dart
verify(mockService.getPantryItems()).called(1);
```

## Examples

### Testing Network Connectivity

```dart
test('should handle offline state', () async {
  TestUtilities.setupMockConnectivity(
    mockConnectivity, 
    ConnectivityResult.none
  );
  
  final isOnline = await ConnectivityUtils.isOnline();
  expect(isOnline, isFalse);
});
```

### Testing HTTP Operations

```dart
test('should handle HTTP errors', () async {
  TestUtilities.setupMockHttpError(mockClient, 404, 'Not Found');
  
  expect(
    () => service.getData(),
    throwsA(isA<Exception>()),
  );
});
```

### Testing Service Integration

```dart
test('should sync data when online', () async {
  final items = TestUtilities.createSamplePantryItems();
  TestUtilities.setupMockPantryService(mockPantryService, items);
  TestUtilities.setupMockOfflineStorage(mockStorage, []);
  
  await syncService.syncWithServer(mockPantryService);
  
  verify(mockPantryService.getPantryItems()).called(1);
  verify(mockStorage.bulkInsertPantryItems(items, markAsSynced: true)).called(1);
});
```

## Troubleshooting

### Build Runner Issues
If mock generation fails, try:
```bash
flutter clean
flutter pub get
dart run build_runner clean
dart run build_runner build --delete-conflicting-outputs
```

### Import Conflicts
Always import from the main mocks file to avoid conflicts:
```dart
import '../mocks/mocks.dart';  // Good
import '../mocks/all_mocks.mocks.dart';  // Avoid direct imports
```

### Mock Verification Failures
Ensure you're using the exact same objects:
```dart
// Setup and verification must use same mock instance
when(mockService.method()).thenAnswer((_) async => result);
verify(mockService.method()).called(1);
```

## Contributing

When adding new services:

1. Add the service to the appropriate mock definition file
2. Run `build_runner` to generate mocks
3. Add utility methods to `TestUtilities` if needed
4. Update this README with new mock information
5. Create example tests demonstrating usage
