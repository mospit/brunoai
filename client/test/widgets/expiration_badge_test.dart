import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../lib/widgets/expiration_badge_widget.dart';
import '../../lib/features/pantry/models/pantry_item.dart';
import '../../lib/features/pantry/models/pantry_category.dart';
import '../mocks/test_utilities.dart';

void main() {
  group('ExpirationBadgeWidget Tests', () {
    
    Widget createTestableWidget(PantryItem item) {
      return MaterialApp(
        home: Scaffold(
          body: ExpirationBadgeWidget(pantryItem: item),
        ),
      );
    }

    group('Expiration Badge Color Tests', () {
      testWidgets('should display red badge with "EXPIRED" text for expired items', (WidgetTester tester) async {
        final expiredItem = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().subtract(const Duration(days: 2)),
        );

        await tester.pumpWidget(createTestableWidget(expiredItem));

        // Verify the badge is displayed
        expect(find.byType(ExpirationBadgeWidget), findsOneWidget);
        expect(find.text('EXPIRED'), findsOneWidget);
        expect(find.byIcon(Icons.warning), findsOneWidget);

        // Verify the container styling (red background)
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('EXPIRED'),
            matching: find.byType(Container),
          ).first,
        );
        expect(container.decoration, isA<BoxDecoration>());
        final decoration = container.decoration as BoxDecoration;
        
        // The color should be red (#FF4444 converted to Color)
        expect(decoration.color?.value, 0xFFFF4444);
      });

      testWidgets('should display orange badge with "TODAY" text for items expiring today', (WidgetTester tester) async {
        final today = DateTime.now();
        final todayItem = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime(today.year, today.month, today.day),
        );

        await tester.pumpWidget(createTestableWidget(todayItem));

        expect(find.byType(ExpirationBadgeWidget), findsOneWidget);
        expect(find.text('TODAY'), findsOneWidget);
        expect(find.byIcon(Icons.schedule), findsOneWidget);

        // Verify the container styling (orange background)
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('TODAY'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        
        // The color should be orange (#FF8800 converted to Color)
        expect(decoration.color?.value, 0xFFFF8800);
      });

      testWidgets('should display yellow badge with days left for items expiring within 3 days', (WidgetTester tester) async {
        final warningItem = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 2)),
        );

        await tester.pumpWidget(createTestableWidget(warningItem));

        expect(find.byType(ExpirationBadgeWidget), findsOneWidget);
        expect(find.text('2d left'), findsOneWidget);
        expect(find.byIcon(Icons.schedule), findsOneWidget);

        // Verify the container styling (yellow background)
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('2d left'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        
        // The color should be yellow (#FFD700 converted to Color)
        expect(decoration.color?.value, 0xFFFFD700);
      });

      testWidgets('should display green badge with days left for items expiring after 3 days', (WidgetTester tester) async {
        final normalItem = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 7)),
        );

        await tester.pumpWidget(createTestableWidget(normalItem));

        expect(find.byType(ExpirationBadgeWidget), findsOneWidget);
        expect(find.text('7d left'), findsOneWidget);
        expect(find.byIcon(Icons.check_circle), findsOneWidget);

        // Verify the container styling (green background)
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('7d left'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        
        // The color should be green (#4CAF50 converted to Color)
        expect(decoration.color?.value, 0xFF4CAF50);
      });

      testWidgets('should display grey badge with "No date" for items without expiration date', (WidgetTester tester) async {
        final noDateItem = TestUtilities.createSamplePantryItem(
          expirationDate: null,
        );

        await tester.pumpWidget(createTestableWidget(noDateItem));

        expect(find.byType(ExpirationBadgeWidget), findsOneWidget);
        expect(find.text('No date'), findsOneWidget);
        expect(find.byIcon(Icons.help), findsOneWidget);

        // Verify the container styling (grey background)
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('No date'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        
        // The color should be grey (#9E9E9E converted to Color)
        expect(decoration.color?.value, 0xFF9E9E9E);
      });
    });

    group('Expiration Badge State Transitions', () {
      testWidgets('should show correct badge for item expiring in 1 day', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 1)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('1d left'), findsOneWidget);
        expect(find.byIcon(Icons.schedule), findsOneWidget);
        
        // Should be in warning state (yellow)
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('1d left'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        expect(decoration.color?.value, 0xFFFFD700);
      });

      testWidgets('should show correct badge for item expiring in exactly 3 days', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('3d left'), findsOneWidget);
        expect(find.byIcon(Icons.schedule), findsOneWidget);
        
        // Should be in warning state (yellow) - boundary condition
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('3d left'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        expect(decoration.color?.value, 0xFFFFD700);
      });

      testWidgets('should show correct badge for item expiring in 4 days', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 4)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('4d left'), findsOneWidget);
        expect(find.byIcon(Icons.check_circle), findsOneWidget);
        
        // Should be in normal state (green) - just over the warning threshold
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('4d left'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        expect(decoration.color?.value, 0xFF4CAF50);
      });

      testWidgets('should show correct badge for item expired 1 day ago', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().subtract(const Duration(days: 1)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        expect(find.text('EXPIRED'), findsOneWidget);
        expect(find.byIcon(Icons.warning), findsOneWidget);
        
        // Should be in expired state (red)
        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('EXPIRED'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        expect(decoration.color?.value, 0xFFFF4444);
      });
    });

    group('Badge Styling Tests', () {
      testWidgets('should have correct text color for expired badge', (WidgetTester tester) async {
        final expiredItem = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().subtract(const Duration(days: 1)),
        );

        await tester.pumpWidget(createTestableWidget(expiredItem));

        final textWidget = tester.widget<Text>(find.text('EXPIRED'));
        expect(textWidget.style?.color?.value, 0xFFFFFFFF); // White text
        expect(textWidget.style?.fontWeight, FontWeight.bold);
      });

      testWidgets('should have correct text color for warning badge', (WidgetTester tester) async {
        final warningItem = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 2)),
        );

        await tester.pumpWidget(createTestableWidget(warningItem));

        final textWidget = tester.widget<Text>(find.text('2d left'));
        expect(textWidget.style?.color?.value, 0xFF000000); // Black text for warning
        expect(textWidget.style?.fontWeight, FontWeight.bold);
      });

      testWidgets('should have correct text color for normal badge', (WidgetTester tester) async {
        final normalItem = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 7)),
        );

        await tester.pumpWidget(createTestableWidget(normalItem));

        final textWidget = tester.widget<Text>(find.text('7d left'));
        expect(textWidget.style?.color?.value, 0xFFFFFFFF); // White text for normal
        expect(textWidget.style?.fontWeight, FontWeight.bold);
      });

      testWidgets('should have correct border radius and shadow', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('3d left'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        
        expect(decoration.borderRadius, BorderRadius.circular(12));
        expect(decoration.boxShadow, isNotNull);
        expect(decoration.boxShadow?.length, 1);
      });

      testWidgets('should display icon with correct size', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        final iconWidget = tester.widget<Icon>(find.byIcon(Icons.schedule));
        expect(iconWidget.size, 14.0); // fontSize (12) + 2
      });
    });

    group('Custom Badge Properties Tests', () {
      testWidgets('should respect custom fontSize', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ExpirationBadgeWidget(
              pantryItem: item,
              fontSize: 16.0,
            ),
          ),
        ));

        final textWidget = tester.widget<Text>(find.text('3d left'));
        expect(textWidget.style?.fontSize, 16.0);

        final iconWidget = tester.widget<Icon>(find.byIcon(Icons.schedule));
        expect(iconWidget.size, 18.0); // fontSize (16) + 2
      });

      testWidgets('should respect custom padding', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        const customPadding = EdgeInsets.all(20.0);

        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ExpirationBadgeWidget(
              pantryItem: item,
              padding: customPadding,
            ),
          ),
        ));

        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('3d left'),
            matching: find.byType(Container),
          ).first,
        );
        expect(container.padding, customPadding);
      });

      testWidgets('should respect custom borderRadius', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 3)),
        );

        const customBorderRadius = BorderRadius.all(Radius.circular(20.0));

        await tester.pumpWidget(MaterialApp(
          home: Scaffold(
            body: ExpirationBadgeWidget(
              pantryItem: item,
              borderRadius: customBorderRadius,
            ),
          ),
        ));

        final container = tester.widget<Container>(
          find.ancestor(
            of: find.text('3d left'),
            matching: find.byType(Container),
          ).first,
        );
        final decoration = container.decoration as BoxDecoration;
        expect(decoration.borderRadius, customBorderRadius);
      });
    });

    group('Badge Content Verification', () {
      testWidgets('should display both icon and text', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 5)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        // Verify both icon and text are in the same Row
        final rowWidget = tester.widget<Row>(
          find.ancestor(
            of: find.text('5d left'),
            matching: find.byType(Row),
          ),
        );
        expect(rowWidget.mainAxisSize, MainAxisSize.min);
        
        // Verify both elements exist
        expect(find.byIcon(Icons.check_circle), findsOneWidget);
        expect(find.text('5d left'), findsOneWidget);
      });

      testWidgets('should have proper spacing between icon and text', (WidgetTester tester) async {
        final item = TestUtilities.createSamplePantryItem(
          expirationDate: DateTime.now().add(const Duration(days: 5)),
        );

        await tester.pumpWidget(createTestableWidget(item));

        // Verify SizedBox exists between icon and text (find the one with width 4.0)
        final sizedBoxes = find.byType(SizedBox);
        expect(sizedBoxes, findsAtLeastNWidgets(1));
        
        // Find the SizedBox with width 4.0 (the spacing one)
        final spacingSizedBox = tester.widgetList<SizedBox>(sizedBoxes)
            .firstWhere((widget) => widget.width == 4.0);
        expect(spacingSizedBox.width, 4.0);
      });
    });
  });
}
