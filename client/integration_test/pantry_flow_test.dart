import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:client/features/pantry/services/pantry_service.dart';
import 'package:client/features/pantry/models/pantry_item.dart';
import 'package:client/features/pantry/models/pantry_category.dart';
import 'package:client/features/pantry/bloc/pantry_bloc.dart';
import 'package:client/features/pantry/screens/pantry_screen.dart';
import 'package:client/services/product_lookup_service.dart';

class MockPantryService extends Mock implements PantryService {}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Pantry Flow Test', () {
    late MockPantryService mockPantryService;

    setUp(() {
      mockPantryService = MockPantryService();
    });

    testWidgets('Add, Edit and Delete Item flow', (WidgetTester tester) async {
      // Create test pantry items
      final testItem = PantryItem(
        id: 1,
        name: 'Test Item',
        quantity: 10.0,
        unit: 'piece',
        category: PantryCategory.fromLabel('Pantry'),
      );
      
      final updatedItem = PantryItem(
        id: 1,
        name: 'Updated Test Item',
        quantity: 15.0,
        unit: 'piece',
        category: PantryCategory.fromLabel('Pantry'),
      );

      // Mock service responses
      when(mockPantryService.getPantryItems())
        .thenAnswer((_) async => []);
      
      when(mockPantryService.addPantryItem(any as PantryItem))
        .thenAnswer((_) async => testItem);
      
      when(mockPantryService.updatePantryItem(any as PantryItem))
        .thenAnswer((_) async => updatedItem);
      
      when(mockPantryService.deletePantryItem(any as int))
        .thenAnswer((_) async => true);

      // Create the app with mocked services
      final app = MaterialApp(
        home: MultiBlocProvider(
          providers: [
            BlocProvider(
              create: (context) => PantryBloc(pantryService: mockPantryService),
            ),
          ],
          child: MultiProvider(
            providers: [
              Provider<PantryService>.value(value: mockPantryService),
              Provider<ProductLookupService>(create: (_) => ProductLookupService()),
            ],
            child: const PantryScreen(),
          ),
        ),
      );
      
      await tester.pumpWidget(app);

      // Perform UI operations to add an item
await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextFormField).at(0), 'Test Item');
      await tester.enterText(find.byType(TextFormField).at(1), '10');
      await tester.tap(find.text('Add to Pantry'));
      await tester.pumpAndSettle();

      expect(find.text('Test Item'), findsOneWidget);

      // Wait a bit for the item to be added to the list
      await tester.pumpAndSettle();
      
      // Verify item is added to list
      expect(find.text('Test Item'), findsOneWidget);

      // 2. Test Editing an Item
      // Mock list response to return the item we just added
      when(mockPantryService.getPantryItems())
        .thenAnswer((_) async => [testItem]);
      
      // Refresh the screen to see the item
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();
      
      // Tap on item to edit it
      await tester.tap(find.text('Test Item'));
      await tester.pumpAndSettle();

      // Clear the name field and enter new name
      await tester.enterText(find.byType(TextFormField).at(0), 'Updated Test Item');
      await tester.tap(find.text('Update Item'));
      await tester.pumpAndSettle();

      // Navigate back to pantry screen
      await tester.pageBack();
      await tester.pumpAndSettle();
      
      // Mock the updated list
      when(mockPantryService.getPantryItems())
        .thenAnswer((_) async => [updatedItem]);
        
      // Refresh to see the updated item
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();

      expect(find.text('Updated Test Item'), findsOneWidget);

      // 3. Test Deleting an Item
      // Tap on delete button for the item
      await tester.tap(find.byIcon(Icons.delete_outline));
      await tester.pumpAndSettle();
      
      // Confirm deletion
      await tester.tap(find.text('Delete'));
      await tester.pumpAndSettle();
      
      // Mock empty list after deletion
      when(mockPantryService.getPantryItems())
        .thenAnswer((_) async => []);
        
      // Refresh to see the item is gone
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();

      expect(find.text('Updated Test Item'), findsNothing);
    });
    
    testWidgets('Error handling tests', (WidgetTester tester) async {
      // Test network error when adding item
      when(mockPantryService.getPantryItems())
        .thenAnswer((_) async => []);
      
      when(mockPantryService.addPantryItem(any as PantryItem))
        .thenThrow(Exception('Network error while adding pantry item'));

      final app = MaterialApp(
        home: MultiBlocProvider(
          providers: [
            BlocProvider(
              create: (context) => PantryBloc(pantryService: mockPantryService),
            ),
          ],
          child: MultiProvider(
            providers: [
              Provider<PantryService>.value(value: mockPantryService),
              Provider<ProductLookupService>(create: (_) => ProductLookupService()),
            ],
            child: const PantryScreen(),
          ),
        ),
      );
      
      await tester.pumpWidget(app);
      await tester.pumpAndSettle();

      // Try to add an item that will fail
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextFormField).at(0), 'Failed Item');
      await tester.enterText(find.byType(TextFormField).at(1), '10');
      await tester.enterText(find.byType(TextFormField).at(2), 'piece');
      await tester.tap(find.text('Add to Pantry'));
      await tester.pumpAndSettle();

      // Should show error message
      expect(find.text('Error: Exception: Network error while adding pantry item'), findsOneWidget);
    });
    
    testWidgets('Validation error tests', (WidgetTester tester) async {
      when(mockPantryService.getPantryItems())
        .thenAnswer((_) async => []);

      final app = MaterialApp(
        home: MultiBlocProvider(
          providers: [
            BlocProvider(
              create: (context) => PantryBloc(pantryService: mockPantryService),
            ),
          ],
          child: MultiProvider(
            providers: [
              Provider<PantryService>.value(value: mockPantryService),
              Provider<ProductLookupService>(create: (_) => ProductLookupService()),
            ],
            child: const PantryScreen(),
          ),
        ),
      );
      
      await tester.pumpWidget(app);
      await tester.pumpAndSettle();

      // Try to add an item with invalid data (empty name)
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Leave name empty and try to submit
      await tester.enterText(find.byType(TextFormField).at(1), '10');
      await tester.enterText(find.byType(TextFormField).at(2), 'piece');
      await tester.tap(find.text('Add to Pantry'));
      await tester.pumpAndSettle();

      // Should show validation error
      expect(find.text('Please enter an item name'), findsOneWidget);
      
      // Try with invalid quantity (empty)
      await tester.enterText(find.byType(TextFormField).at(0), 'Test Item');
      await tester.enterText(find.byType(TextFormField).at(1), '');
      await tester.tap(find.text('Add to Pantry'));
      await tester.pumpAndSettle();

      // Should show quantity validation error
      expect(find.text('Please enter a valid quantity'), findsOneWidget);
    });
  });
}

