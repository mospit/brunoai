import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:http/http.dart' as http;

// Import mock classes (will be generated)
import 'all_mocks.mocks.dart';

// Import models
import 'package:client/features/pantry/models/pantry_item.dart';
import 'package:client/features/pantry/models/pantry_category.dart';
import 'package:client/models/product.dart';

/// Test utilities and helper functions for mocking and test setup
class TestUtilities {
  /// Create a mock HTTP response with given status code and body
  static http.Response createMockHttpResponse(int statusCode, String body) {
    return http.Response(body, statusCode);
  }

  /// Create a sample PantryItem for testing
  static PantryItem createSamplePantryItem({
    int? id,
    String name = 'Test Item',
    double quantity = 1.0,
    String unit = 'piece',
    PantryCategory? category,
    DateTime? expirationDate,
  }) {
    return PantryItem(
      id: id,
      name: name,
      quantity: quantity,
      unit: unit,
      category: category,
      expirationDate: expirationDate,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  /// Create a sample PantryCategory for testing
  static PantryCategory createSampleCategory({
    int id = 1,
    String name = 'Test Category',
    String description = 'Test category description',
    String icon = 'test_icon',
    String color = '#FF0000',
  }) {
    return PantryCategory(
      id: id,
      name: name,
      description: description,
      icon: icon,
      color: color,
    );
  }

  /// Create a sample Product for testing
  static Product createSampleProduct({
    String barcode = '1234567890123',
    String name = 'Test Product',
    String brand = 'Test Brand',
    String category = 'Food',
    String? description,
    List<String>? images,
  }) {
    return Product(
      barcode: barcode,
      name: name,
      brand: brand,
      category: category,
      description: description,
      images: images,
    );
  }

  /// Setup mock connectivity with specified result
  static void setupMockConnectivity(
    MockConnectivity mockConnectivity,
    ConnectivityResult result,
  ) {
    when(mockConnectivity.checkConnectivity())
        .thenAnswer((_) async => result);
  }

  /// Setup mock HTTP client with success response
  static void setupMockHttpSuccess(
    MockClient mockClient,
    String responseBody, {
    int statusCode = 200,
  }) {
    when(mockClient.get(any, headers: anyNamed('headers')))
        .thenAnswer((_) async => http.Response(responseBody, statusCode));
  }

  /// Setup mock HTTP client with error response
  static void setupMockHttpError(
    MockClient mockClient,
    int statusCode,
    String errorBody,
  ) {
    when(mockClient.get(any, headers: anyNamed('headers')))
        .thenAnswer((_) async => http.Response(errorBody, statusCode));
  }

  /// Setup mock HTTP client to throw exception
  static void setupMockHttpException(
    MockClient mockClient,
    Exception exception,
  ) {
    when(mockClient.get(any, headers: anyNamed('headers')))
        .thenThrow(exception);
  }

  /// Setup mock PantryService with predefined return values
  static void setupMockPantryService(
    MockPantryService mockPantryService,
    List<PantryItem> items,
  ) {
    when(mockPantryService.getPantryItems())
        .thenAnswer((_) async => items);
  }

  /// Setup mock CategoryService with predefined return values
  static void setupMockCategoryService(
    MockCategoryService mockCategoryService,
    List<PantryCategory> categories,
  ) {
    when(mockCategoryService.getCategories())
        .thenAnswer((_) async => categories);
  }

  /// Setup mock OfflineStorageService with predefined return values
  static void setupMockOfflineStorage(
    MockOfflineStorageService mockOfflineStorage,
    List<PantryItem> items,
  ) {
    when(mockOfflineStorage.getAllPantryItems())
        .thenAnswer((_) async => items);
  }

  /// Create a list of sample pantry items for testing
  static List<PantryItem> createSamplePantryItems({int count = 3}) {
    return List.generate(count, (index) => createSamplePantryItem(
      id: index + 1,
      name: 'Test Item ${index + 1}',
      quantity: (index + 1).toDouble(),
    ));
  }

  /// Create a list of sample categories for testing
  static List<PantryCategory> createSampleCategories({int count = 3}) {
    final categoryNames = ['Dairy', 'Meat', 'Vegetables', 'Fruits', 'Grains'];
    return List.generate(count, (index) => createSampleCategory(
      id: index + 1,
      name: categoryNames[index % categoryNames.length],
      description: 'Test ${categoryNames[index % categoryNames.length]} category',
    ));
  }

  /// Verify that a mock was called with specific arguments
  static void verifyMockCall<T>(
    Mock mock,
    Function method, {
    int times = 1,
  }) {
    verify(method).called(times);
  }

  /// Reset all mocks to their initial state
  static void resetMocks(List<Mock> mocks) {
    for (final mock in mocks) {
      reset(mock);
    }
  }
}

/// Common test constants
class TestConstants {
  static const String mockBaseUrl = 'http://test-api.example.com';
  static const String validBarcode = '1234567890123';
  static const String invalidBarcode = 'invalid';
  
  static const Map<String, String> mockHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  static const String mockPantryItemJson = '''
  {
    "id": 1,
    "name": "Test Item",
    "quantity": 1.0,
    "unit": "piece",
    "category": "Food",
    "expiration_date": "2024-12-31T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
  ''';

  static const String mockCategoryJson = '''
  {
    "id": 1,
    "name": "Test Category",
    "description": "Test category description",
    "icon": "test_icon",
    "color": "#FF0000"
  }
  ''';

  static const String mockProductJson = '''
  {
    "barcode": "1234567890123",
    "name": "Test Product",
    "brand": "Test Brand",
    "category": "Food",
    "description": "Test product description"
  }
  ''';
}
