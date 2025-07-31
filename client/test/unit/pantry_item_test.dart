import 'package:flutter_test/flutter_test.dart';
import '../../lib/features/pantry/models/pantry_item.dart';
import '../../lib/features/pantry/models/pantry_category.dart';

void main() {
  group('PantryItem', () {
    group('model creation', () {
      test('should create pantry item with required fields', () {
        final item = PantryItem(
          name: 'Test Item',
          quantity: 2.0,
          unit: 'pieces',
        );

        expect(item.name, 'Test Item');
        expect(item.quantity, 2.0);
        expect(item.unit, 'pieces');
        expect(item.id, null);
        expect(item.category, null);
        expect(item.expirationDate, null);
      });

      test('should create pantry item with all fields', () {
        final expiration = DateTime(2024, 12, 31);
        final created = DateTime(2024, 1, 1);
        
        final item = PantryItem(
          id: 123,
          householdId: 456,
          name: 'Complete Item',
          quantity: 3.5,
          unit: 'kg',
          expirationDate: expiration,
          category: PantryCategory.fromLabel('Dairy'),
          addedBy: 789,
          createdAt: created,
          updatedAt: created,
        );

        expect(item.id, 123);
        expect(item.householdId, 456);
        expect(item.name, 'Complete Item');
        expect(item.quantity, 3.5);
        expect(item.unit, 'kg');
        expect(item.expirationDate, expiration);
        expect(item.category?.name, 'Dairy');
        expect(item.addedBy, 789);
        expect(item.createdAt, created);
        expect(item.updatedAt, created);
      });
    });

    group('JSON serialization', () {
      test('should convert to JSON correctly', () {
        final expiration = DateTime(2024, 12, 31);
        final item = PantryItem(
          id: 123,
          name: 'Test Item',
          quantity: 2.0,
          unit: 'pieces',
          expirationDate: expiration,
          category: PantryCategory.fromLabel('Other'), // Using 'Other' as it's a valid category
        );

        final json = item.toJson();

        expect(json['id'], 123);
        expect(json['name'], 'Test Item');
        expect(json['quantity'], 2.0);
        expect(json['unit'], 'pieces');
        expect(json['expiration_date'], expiration.toIso8601String());
        // Note: category is not serialized to JSON directly in this model
      });

      test('should handle null values in JSON conversion', () {
        final item = PantryItem(
          name: 'Minimal Item',
          quantity: 1.0,
          unit: 'piece',
        );

        final json = item.toJson();

        expect(json['id'], null);
        expect(json['name'], 'Minimal Item');
        expect(json['expiration_date'], null);
        expect(json['category'], null);
      });
    });

    group('JSON deserialization', () {
      test('should create from JSON correctly', () {
        final json = {
          'id': 123,
          'household_id': 456,
          'name': 'JSON Item',
          'quantity': 2.5,
          'unit': 'kg',
          'expiration_date': '2024-12-31T00:00:00.000Z',
          'category': {
            'id': 2,
            'name': 'Vegetables',
            'description': 'Fresh and frozen vegetables',
            'icon': '🥕',
            'color': '#4ECDC4'
          },
          'added_by_user_id': 789,
          'created_at': '2024-01-01T00:00:00.000Z',
          'updated_at': '2024-01-01T00:00:00.000Z',
        };

        final item = PantryItem.fromJson(json);

        expect(item.id, 123);
        expect(item.householdId, 456);
        expect(item.name, 'JSON Item');
        expect(item.quantity, 2.5);
        expect(item.unit, 'kg');
        expect(item.expirationDate, DateTime.parse('2024-12-31T00:00:00.000Z'));
        expect(item.category?.name, 'Vegetables');
        expect(item.addedBy, 789);
        expect(item.createdAt, DateTime.parse('2024-01-01T00:00:00.000Z'));
        expect(item.updatedAt, DateTime.parse('2024-01-01T00:00:00.000Z'));
      });

      test('should handle missing fields in JSON', () {
        final json = {
          'name': 'Minimal JSON Item',
          'quantity': 1,
          'unit': 'piece',
        };

        final item = PantryItem.fromJson(json);

        expect(item.name, 'Minimal JSON Item');
        expect(item.quantity, 1.0);
        expect(item.unit, 'piece');
        expect(item.id, null);
        expect(item.category, null);
        expect(item.expirationDate, null);
      });

      test('should handle null quantity gracefully', () {
        final json = {
          'name': 'Zero Quantity Item',
          'quantity': null,
          'unit': 'piece',
        };

        final item = PantryItem.fromJson(json);

        expect(item.quantity, 0.0);
        expect(item.unit, 'piece');
      });

      test('should handle empty unit gracefully', () {
        final json = {
          'name': 'No Unit Item',
          'quantity': 1,
          'unit': null,
        };

        final item = PantryItem.fromJson(json);

        expect(item.quantity, 1.0);
        expect(item.unit, '');
      });
    });

    group('copyWith functionality', () {
      test('should copy with updated fields', () {
        final original = PantryItem(
          id: 123,
          name: 'Original Item',
          quantity: 1.0,
          unit: 'piece',
          category: PantryCategory.fromLabel('Other'),
        );

        final updated = original.copyWith(
          name: 'Updated Item',
          quantity: 2.0,
        );

        expect(updated.id, 123); // unchanged
        expect(updated.name, 'Updated Item'); // changed
        expect(updated.quantity, 2.0); // changed
        expect(updated.unit, 'piece'); // unchanged
        expect(updated.category?.name, 'Other'); // unchanged
      });

      test('should copy without changes when no parameters provided', () {
        final original = PantryItem(
          id: 123,
          name: 'Original Item',
          quantity: 1.0,
          unit: 'piece',
        );

        final copy = original.copyWith();

        expect(copy.id, original.id);
        expect(copy.name, original.name);
        expect(copy.quantity, original.quantity);
        expect(copy.unit, original.unit);
      });
    });

    group('toString functionality', () {
      test('should provide readable string representation', () {
        final expiration = DateTime(2024, 12, 31);
        final item = PantryItem(
          id: 123,
          name: 'Test Item',
          quantity: 2.0,
          unit: 'pieces',
          expirationDate: expiration,
          category: PantryCategory.fromLabel('Other'),
        );

        final stringRep = item.toString();

        expect(stringRep, contains('123'));
        expect(stringRep, contains('Test Item'));
        expect(stringRep, contains('2.0'));
        expect(stringRep, contains('pieces'));
        expect(stringRep, contains('Other'));
      });
    });
  });
}
