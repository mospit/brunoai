import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

// Import all mocks and utilities
import 'mocks.dart';

// Import models and services to test
import '../../lib/features/pantry/models/pantry_item.dart';
import '../../lib/features/pantry/models/pantry_category.dart';

/// Example test demonstrating how to use the generated mocks
/// 
/// This file shows best practices for:
/// - Setting up mocks with TestUtilities
/// - Using mock services in tests
/// - Verifying mock interactions
/// - Testing with sample data
void main() {
  group('Mock Usage Examples', () {
    late MockPantryService mockPantryService;
    late MockCategoryService mockCategoryService;
    late MockConnectivity mockConnectivity;
    late MockClient mockHttpClient;
    late MockOfflineStorageService mockOfflineStorage;

    setUp(() {
      // Initialize all mocks
      mockPantryService = MockPantryService();
      mockCategoryService = MockCategoryService();
      mockConnectivity = MockConnectivity();
      mockHttpClient = MockClient();
      mockOfflineStorage = MockOfflineStorageService();
    });

    tearDown(() {
      // Reset mocks after each test
      TestUtilities.resetMocks([
        mockPantryService,
        mockCategoryService,
        mockConnectivity,
        mockHttpClient,
        mockOfflineStorage,
      ]);
    });

    group('PantryService Mock Examples', () {
      test('should return mock pantry items', () async {
        // Arrange
        final sampleItems = TestUtilities.createSamplePantryItems(count: 3);
        TestUtilities.setupMockPantryService(mockPantryService, sampleItems);

        // Act
        final result = await mockPantryService.getPantryItems();

        // Assert
        expect(result, hasLength(3));
        expect(result.first.name, equals('Test Item 1'));
        verify(mockPantryService.getPantryItems()).called(1);
      });

      test('should handle pantry item creation', () async {
        // Arrange
        final newItem = TestUtilities.createSamplePantryItem(
          name: 'New Test Item',
          quantity: 5.0,
        );
        when(mockPantryService.addPantryItem(any))
            .thenAnswer((_) async => newItem);

        // Act
        final result = await mockPantryService.addPantryItem(newItem);

        // Assert
        expect(result.name, equals('New Test Item'));
        expect(result.quantity, equals(5.0));
        verify(mockPantryService.addPantryItem(newItem)).called(1);
      });
    });

    group('CategoryService Mock Examples', () {
      test('should return mock categories', () async {
        // Arrange
        final sampleCategories = TestUtilities.createSampleCategories(count: 2);
        TestUtilities.setupMockCategoryService(mockCategoryService, sampleCategories);

        // Act
        final result = await mockCategoryService.getCategories();

        // Assert
        expect(result, hasLength(2));
        expect(result.first.name, equals('Dairy'));
        verify(mockCategoryService.getCategories()).called(1);
      });
    });

    group('Connectivity Mock Examples', () {
      test('should mock WiFi connection', () async {
        // Arrange
        TestUtilities.setupMockConnectivity(
          mockConnectivity,
          ConnectivityResult.wifi,
        );

        // Act
        final result = await mockConnectivity.checkConnectivity();

        // Assert
        expect(result, equals(ConnectivityResult.wifi));
        verify(mockConnectivity.checkConnectivity()).called(1);
      });

      test('should mock no connection', () async {
        // Arrange
        TestUtilities.setupMockConnectivity(
          mockConnectivity,
          ConnectivityResult.none,
        );

        // Act
        final result = await mockConnectivity.checkConnectivity();

        // Assert
        expect(result, equals(ConnectivityResult.none));
      });
    });

    group('HTTP Client Mock Examples', () {
      test('should mock successful HTTP response', () async {
        // Arrange
        TestUtilities.setupMockHttpSuccess(
          mockHttpClient,
          TestConstants.mockPantryItemJson,
          statusCode: 200,
        );

        // Act
        final response = await mockHttpClient.get(
          Uri.parse('${TestConstants.mockBaseUrl}/test'),
          headers: TestConstants.mockHeaders,
        );

        // Assert
        expect(response.statusCode, equals(200));
        expect(response.body, contains('Test Item'));
      });

      test('should mock HTTP error response', () async {
        // Arrange
        TestUtilities.setupMockHttpError(
          mockHttpClient,
          404,
          'Not Found',
        );

        // Act
        final response = await mockHttpClient.get(
          Uri.parse('${TestConstants.mockBaseUrl}/test'),
          headers: TestConstants.mockHeaders,
        );

        // Assert
        expect(response.statusCode, equals(404));
        expect(response.body, equals('Not Found'));
      });
    });

    group('Offline Storage Mock Examples', () {
      test('should return mock offline data', () async {
        // Arrange
        final sampleItems = TestUtilities.createSamplePantryItems(count: 2);
        TestUtilities.setupMockOfflineStorage(mockOfflineStorage, sampleItems);

        // Act
        final result = await mockOfflineStorage.getAllPantryItems();

        // Assert
        expect(result, hasLength(2));
        expect(result.first.name, equals('Test Item 1'));
        verify(mockOfflineStorage.getAllPantryItems()).called(1);
      });
    });

    group('Integration Mock Examples', () {
      test('should work with multiple mocks together', () async {
        // Arrange
        final sampleItems = TestUtilities.createSamplePantryItems(count: 1);
        final sampleCategories = TestUtilities.createSampleCategories(count: 1);
        
        TestUtilities.setupMockPantryService(mockPantryService, sampleItems);
        TestUtilities.setupMockCategoryService(mockCategoryService, sampleCategories);
        TestUtilities.setupMockConnectivity(mockConnectivity, ConnectivityResult.wifi);

        // Act
        final items = await mockPantryService.getPantryItems();
        final categories = await mockCategoryService.getCategories();
        final connectivity = await mockConnectivity.checkConnectivity();

        // Assert
        expect(items, hasLength(1));
        expect(categories, hasLength(1));
        expect(connectivity, equals(ConnectivityResult.wifi));

        // Verify all calls were made
        verify(mockPantryService.getPantryItems()).called(1);
        verify(mockCategoryService.getCategories()).called(1);
        verify(mockConnectivity.checkConnectivity()).called(1);
      });
    });
  });
}
