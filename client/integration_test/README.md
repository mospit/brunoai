# Pantry Management Integration Tests

This directory contains integration tests for the Flutter pantry management app that test the complete add/edit/delete flow for pantry items.

## Test Coverage

### 1. Add/Edit/Delete Flow Test (`pantry_flow_test.dart`)
Tests the complete workflow of pantry item management:
- **Add Item**: Verifies that a new pantry item can be added and appears in the list
- **Edit Item**: Tests editing an existing item and verifies UI updates correctly
- **Delete Item**: Tests deletion of an item and verifies it disappears from the list

### 2. Error Handling Tests
- **Network Errors**: Tests behavior when backend services are unavailable
- **Validation Errors**: Tests form validation for required fields and invalid input

## How to Run

### Prerequisites
1. Ensure you have Flutter installed and configured
2. Install dependencies: `flutter pub get`
3. Generate mock files: `dart run build_runner build`

### Running the Tests

#### Option 1: Command Line
```bash
# Run all integration tests
flutter test integration_test/

# Run specific test file
flutter test integration_test/pantry_flow_test.dart
```

#### Option 2: Using Test Driver
```bash
# Run with driver (useful for debugging)
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/pantry_flow_test.dart
```

### Test Structure

The tests use a mocked `PantryService` to simulate backend responses without requiring a real backend connection. This allows for:

- **Predictable test results**: Tests run consistently regardless of network conditions
- **Fast execution**: No real network calls are made
- **Error simulation**: Can easily test error conditions

### Mock Configuration

The tests use `mockito` to create mock services:
- `MockPantryService`: Mocks CRUD operations for pantry items
- Responses are configured to return specific test data
- Error conditions are simulated by throwing exceptions

### Test Scenarios

1. **Happy Path**: Complete add → edit → delete workflow
2. **Network Failures**: Service calls that throw exceptions
3. **Validation Failures**: Form validation with empty or invalid fields
4. **UI State Verification**: Ensures UI correctly reflects data changes

## Understanding the Tests

Each test follows this pattern:
1. **Setup**: Configure mock service responses
2. **Action**: Perform UI interactions (tap buttons, enter text)
3. **Verification**: Assert expected UI state or content

The tests interact with actual Flutter widgets but use mocked data services, providing a good balance between testing real user interactions and maintaining test reliability.
