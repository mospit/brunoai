/// Convenience exports for all mock classes and test utilities
/// 
/// This file provides a single import point for all mock classes and test
/// utilities used throughout the Bruno AI test suite.
/// 
/// Usage:
/// ```dart
/// import 'package:client/test/mocks/mocks.dart';
/// 
/// void main() {
///   group('MyTests', () {
///     late MockPantryService mockPantryService;
///     late MockConnectivity mockConnectivity;
///     
///     setUp(() {
///       mockPantryService = MockPantryService();
///       mockConnectivity = MockConnectivity();
///     });
///     
///     test('example test', () async {
///       // Use TestUtilities for setup
///       final sampleItems = TestUtilities.createSamplePantryItems();
///       TestUtilities.setupMockPantryService(mockPantryService, sampleItems);
///       
///       // Your test logic here
///     });
///   });
/// }
/// ```

// Export all generated mock classes (only main file to avoid conflicts)
export 'all_mocks.mocks.dart';

// Export test utilities and constants
export 'test_utilities.dart';

// Individual mock files are not exported to avoid naming conflicts
// since all mocks are already available in all_mocks.mocks.dart
