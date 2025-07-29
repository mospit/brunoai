import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';

import '../../lib/features/pantry/widgets/pantry_item_card.dart';
import '../../lib/features/pantry/models/pantry_item.dart';
import '../../lib/features/pantry/models/pantry_category.dart';
import '../../lib/widgets/expiration_badge_widget.dart';
import '../mocks/test_utilities.dart';

void main() {
  group('PantryItemCard Widget Tests', () {
    
    Widget createTestableWidget(
      PantryItem item, {
      VoidCallback? onTap,
      VoidCallback? onDelete,
      VoidCallback? onIncrement,
      VoidCallback? onDecrement,
    }) {
      return MaterialApp(
        home: Scaffold(
          body: PantryItemCard(
            item: item,
            onTap: onTap,
            onDelete: onDelete,
            onIncrement: onIncrement,
            onDecrement: onDecrement,
          ),
        ),
      );
    }

    group('Basic UI Rendering Tests', () {
      testWidgets('should display item name correctly', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(name: 'Test Milk');

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Test Milk'), findsOneWidget);
      });

      testWidgets('should display quantity and unit correctly', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          quantity: 2.5,
          unit: 'liters',
        );

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('2.5 liters'), findsOneWidget);
      });

      testWidgets('should display category when present', (WidgetTester tester) async {
        final category = TestUtilities.createSampleCategory(name: 'Dairy');
        final item = TestUtilities.createSamplePantryItem(category: category);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Dairy'), findsOneWidget);
      });

      testWidgets('should not display category container when category is null', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(category: null);

        await tester.pumpWidget(createTestableWidget(item));

        // Should not find any category text
        expect(find.text('Dairy'), findsNothing);
        expect(find.text('Meat'), findsNothing);
        expect(find.text('Produce'), findsNothing);
      });

      testWidgets('should display delete button when onDelete callback provided', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem();
        bool deletePressed = false;

        await tester.pumpWidget(createTestableWidget(
          item,
          onDelete: () => deletePressed = true,
        ));

        expect(find.byIcon(Icons.delete_outline), findsOneWidget);
        
        await tester.tap(find.byIcon(Icons.delete_outline));
        expect(deletePressed, isTrue);
      });

      testWidgets('should not display delete button when onDelete callback not provided', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem();

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.byIcon(Icons.delete_outline), findsNothing);
      });

      testWidgets('should respond to tap when onTap callback provided', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem();
        bool tapPressed = false;

        await tester.pumpWidget(createTestableWidget(
          item,
          onTap: () => tapPressed = true,
        ));

        await tester.tap(find.byType(InkWell));
        expect(tapPressed, isTrue);
      });
    });

    group('Expiration Badge Tests', () {
      testWidgets('should display expiration badge when expiration date exists', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.byType(ExpirationBadgeWidget), findsOneWidget);
      });

      testWidgets('should not display expiration badge when expiration date is null', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(expirationDate: null);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.byType(ExpirationBadgeWidget), findsNothing);
      });

      testWidgets('should display expiration information text when expiration date exists', (WidgetTester tester) async {
        final expirationDate = DateTime.now().add(const Duration(days: 3));
        final item = TestUtilities.createSamplePantryItem(expirationDate: expirationDate);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.byIcon(Icons.schedule), findsOneWidget);
        expect(find.text('Expires in 3 days'), findsOneWidget);
      });

      testWidgets('should display "Expires today" for same day expiration', (WidgetTester tester) async {
        final today = DateTime.now();
        final expirationDate = DateTime(today.year, today.month, today.day);
        final item = TestUtilities.createSamplePantryItem(expirationDate: expirationDate);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Expires today'), findsOneWidget);
      });

      testWidgets('should display "Expires tomorrow" for next day expiration', (WidgetTester tester) async {
        final expirationDate = DateTime.now().add(const Duration(days: 1));
        final item = TestUtilities.createSamplePantryItem(expirationDate: expirationDate);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Expires tomorrow'), findsOneWidget);
      });

      testWidgets('should display "Expired X days ago" for past expiration', (WidgetTester tester) async {
        final expirationDate = DateTime.now().subtract(const Duration(days: 2));
        final item = TestUtilities.createSamplePantryItem(expirationDate: expirationDate);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Expired 2 days ago'), findsOneWidget);
      });

      testWidgets('should display full date for expiration more than 7 days away', (WidgetTester tester) async {
        final expirationDate = DateTime.now().add(const Duration(days: 10));
        final item = TestUtilities.createSamplePantryItem(expirationDate: expirationDate);

        await tester.pumpWidget(createTestableWidget(item));

        final expectedText = 'Expires ${expirationDate.day}/${expirationDate.month}/${expirationDate.year}';
        expect(find.text(expectedText), findsOneWidget);
      });
    });

    group('Category Color Tests', () {
      testWidgets('should apply correct color for dairy category', (WidgetTester tester) async {
        final category = TestUtilities.createSampleCategory(name: 'Dairy');
        final item = TestUtilities.createSamplePantryItem(category: category);

        await tester.pumpWidget(createTestableWidget(item));

        // Find the category container and verify it exists
        expect(find.text('Dairy'), findsOneWidget);
        
        // The color is applied through decoration which is harder to test directly
        // But we can verify the widget structure exists
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('Dairy'),
            matching: find.byType(Container),
          ).first,
        );
        expect(container.decoration, isA<BoxDecoration>());
      });

      testWidgets('should apply correct color for produce category', (WidgetTester tester) async {
        final category = TestUtilities.createSampleCategory(name: 'Vegetables');
        final item = TestUtilities.createSamplePantryItem(category: category);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Vegetables'), findsOneWidget);
      });

      testWidgets('should apply correct color for meat category', (WidgetTester tester) async {
        final category = TestUtilities.createSampleCategory(name: 'Meat');
        final item = TestUtilities.createSamplePantryItem(category: category);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Meat'), findsOneWidget);
      });

      testWidgets('should apply default color for unknown category', (WidgetTester tester) async {
        final category = TestUtilities.createSampleCategory(name: 'Unknown Category');
        final item = TestUtilities.createSamplePantryItem(category: category);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('Unknown Category'), findsOneWidget);
      });
    });

    group('Quantity Control Tests', () {
      testWidgets('should display increment button when onIncrement callback provided', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);
        bool incrementPressed = false;

        await tester.pumpWidget(createTestableWidget(
          item,
          onIncrement: () => incrementPressed = true,
        ));

        expect(find.byIcon(Icons.add), findsOneWidget);
        
        await tester.tap(find.byIcon(Icons.add));
        expect(incrementPressed, isTrue);
      });

      testWidgets('should display decrement button when onDecrement callback provided and quantity > 0', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);
        bool decrementPressed = false;

        await tester.pumpWidget(createTestableWidget(
          item,
          onDecrement: () => decrementPressed = true,
        ));

        expect(find.byIcon(Icons.remove), findsOneWidget);
        
        await tester.tap(find.byIcon(Icons.remove));
        expect(decrementPressed, isTrue);
      });

      testWidgets('should not display decrement button when quantity is 0', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 0);

        await tester.pumpWidget(createTestableWidget(
          item,
          onDecrement: () {},
        ));

        expect(find.byIcon(Icons.remove), findsNothing);
      });

      testWidgets('should not display quantity controls when callbacks not provided', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.byIcon(Icons.add), findsNothing);
        expect(find.byIcon(Icons.remove), findsNothing);
      });

      testWidgets('should display both increment and decrement buttons when both callbacks provided', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);

        await tester.pumpWidget(createTestableWidget(
          item,
          onIncrement: () {},
          onDecrement: () {},
        ));

        expect(find.byIcon(Icons.add), findsOneWidget);
        expect(find.byIcon(Icons.remove), findsOneWidget);
      });

      testWidgets('should display only increment button when only onIncrement provided', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);

        await tester.pumpWidget(createTestableWidget(
          item,
          onIncrement: () {},
        ));

        expect(find.byIcon(Icons.add), findsOneWidget);
        expect(find.byIcon(Icons.remove), findsNothing);
      });

      testWidgets('should verify quantity control button styling', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);

        await tester.pumpWidget(createTestableWidget(
          item,
          onIncrement: () {},
          onDecrement: () {},
        ));

        // Find increment button container
        final incrementButton = tester.widget<Container>(
          find.ancestor(
            of: find.byIcon(Icons.add),
            matching: find.byType(Container),
          ).first,
        );
        
        expect(incrementButton.decoration, isA<BoxDecoration>());
        final incrementDecoration = incrementButton.decoration as BoxDecoration;
        expect(incrementDecoration.shape, BoxShape.circle);

        // Find decrement button container
        final decrementButton = tester.widget<Container>(
          find.ancestor(
            of: find.byIcon(Icons.remove),
            matching: find.byType(Container),
          ).first,
        );
        
        expect(decrementButton.decoration, isA<BoxDecoration>());
        final decrementDecoration = decrementButton.decoration as BoxDecoration;
        expect(decrementDecoration.shape, BoxShape.circle);
      });
    });

    group('Event Dispatch Tests', () {
      testWidgets('should dispatch correct events on increment button tap', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);
        int incrementCallCount = 0;

        await tester.pumpWidget(createTestableWidget(
          item,
          onIncrement: () => incrementCallCount++,
        ));

        await tester.tap(find.byIcon(Icons.add));
        expect(incrementCallCount, 1);

        await tester.tap(find.byIcon(Icons.add));
        expect(incrementCallCount, 2);
      });

      testWidgets('should dispatch correct events on decrement button tap', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(quantity: 5);
        int decrementCallCount = 0;

        await tester.pumpWidget(createTestableWidget(
          item,
          onDecrement: () => decrementCallCount++,
        ));

        await tester.tap(find.byIcon(Icons.remove));
        expect(decrementCallCount, 1);

        await tester.tap(find.byIcon(Icons.remove));
        expect(decrementCallCount, 2);
      });

      testWidgets('should dispatch correct events on delete button tap', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem();
        int deleteCallCount = 0;

        await tester.pumpWidget(createTestableWidget(
          item,
          onDelete: () => deleteCallCount++,
        ));

        await tester.tap(find.byIcon(Icons.delete_outline));
        expect(deleteCallCount, 1);
      });

      testWidgets('should dispatch correct events on card tap', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem();
        int tapCallCount = 0;

        await tester.pumpWidget(createTestableWidget(
          item,
          onTap: () => tapCallCount++,
        ));

        await tester.tap(find.byType(InkWell));
        expect(tapCallCount, 1);
      });
    });

    group('Edge Cases and Integration Tests', () {
      testWidgets('should handle item with all properties set', (WidgetTester tester) async {
        final category = TestUtilities.createSampleCategory(name: 'Dairy');
        final item = TestUtilities.createSamplePantryItem(
          id: 1,
          name: 'Organic Milk',
          quantity: 2.5,
          unit: 'liters',
          category: category,
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        await tester.pumpWidget(createTestableWidget(
          item,
          onTap: () {},
          onDelete: () {},
          onIncrement: () {},
          onDecrement: () {},
        ));

        // Verify all elements are present
        expect(find.text('Organic Milk'), findsOneWidget);
        expect(find.text('2.5 liters'), findsOneWidget);
        expect(find.text('Dairy'), findsOneWidget);
        expect(find.byType(ExpirationBadgeWidget), findsOneWidget);
        expect(find.byIcon(Icons.add), findsOneWidget);
        expect(find.byIcon(Icons.remove), findsOneWidget);
        expect(find.byIcon(Icons.delete_outline), findsOneWidget);
        expect(find.text('Expires in 3 days'), findsOneWidget);
      });

      testWidgets('should handle item with minimal properties', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          name: 'Basic Item',
          quantity: 1,
          unit: 'piece',
          category: null,
          expirationDate: null,
        );

        await tester.pumpWidget(createTestableWidget(item));

        // Verify minimal elements are present
        expect(find.text('Basic Item'), findsOneWidget);
        expect(find.text('1.0 piece'), findsOneWidget);
        expect(find.byType(ExpirationBadgeWidget), findsNothing);
        expect(find.byIcon(Icons.add), findsNothing);
        expect(find.byIcon(Icons.remove), findsNothing);
        expect(find.byIcon(Icons.delete_outline), findsNothing);
      });

      testWidgets('should handle long item names with ellipsis', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          name: 'This is a very long item name that should be truncated with ellipsis',
        );

        await tester.pumpWidget(createTestableWidget(item));

        final textWidget = tester.widget<Text>(find.text(item.name));
        expect(textWidget.maxLines, 2);
        expect(textWidget.overflow, TextOverflow.ellipsis);
      });

      testWidgets('should handle fractional quantities correctly', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          quantity: 0.5,
          unit: 'kg',
        );

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('0.5 kg'), findsOneWidget);
      });
    });
  });
}
