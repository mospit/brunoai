import 'package:flutter_test/flutter_test.dart';
import 'package:client/models/pantry_category.dart';
import 'package:client/extensions/pantry_category_extension.dart';

void main() {
  group('PantryCategory fromLabel Tests', () {
    test('fromLabel returns null for null input', () {
      final result = PantryCategory.fromLabel(null);
      expect(result, isNull);
    });

    test('fromLabel returns correct category for exact match', () {
      final result = PantryCategory.fromLabel('Fruits');
      expect(result, isNotNull);
      expect(result!.name, equals('Fruits'));
      expect(result.id, equals(1));
    });

    test('fromLabel returns correct category for case-insensitive match', () {
      final result = PantryCategory.fromLabel('DAIRY');
      expect(result, isNotNull);
      expect(result!.name, equals('Dairy'));
      expect(result.id, equals(3));
    });

    test('fromLabel returns correct category for lowercase match', () {
      final result = PantryCategory.fromLabel('vegetables');
      expect(result, isNotNull);
      expect(result!.name, equals('Vegetables'));
      expect(result.id, equals(2));
    });

    test('fromLabel returns unknown category for non-existent label', () {
      final result = PantryCategory.fromLabel('NonExistentCategory');
      expect(result, isNotNull);
      expect(result!.name, equals('Unknown'));
      expect(result.id, equals(0));
    });

    test('fromLabel works with custom categories list', () {
      final customCategories = [
        PantryCategory(id: 100, name: 'Custom Category'),
      ];
      
      final result = PantryCategory.fromLabel('Custom Category', categories: customCategories);
      expect(result, isNotNull);
      expect(result!.name, equals('Custom Category'));
      expect(result.id, equals(100));
    });

    test('fromLabel falls back to unknown with custom categories', () {
      final customCategories = [
        PantryCategory(id: 100, name: 'Custom Category'),
      ];
      
      final result = PantryCategory.fromLabel('NonExistent', categories: customCategories);
      expect(result, isNotNull);
      expect(result!.name, equals('Unknown'));
      expect(result.isUnknown, isTrue);
    });
  });

  group('PantryCategory Extension Tests', () {
    late PantryCategory testCategory;
    late PantryCategory unknownCategory;

    setUp(() {
      testCategory = PantryCategory(
        id: 1,
        name: 'Test Category',
        description: 'Test Description',
      );
      unknownCategory = PantryCategory.unknown;
    });

    test('matchesLabel works correctly', () {
      expect(testCategory.matchesLabel('Test Category'), isTrue);
      expect(testCategory.matchesLabel('test category'), isTrue);
      expect(testCategory.matchesLabel('TEST CATEGORY'), isTrue);
      expect(testCategory.matchesLabel('Different Category'), isFalse);
    });

    test('displayName returns name', () {
      expect(testCategory.displayName, equals('Test Category'));
    });

    test('isUnknown identifies unknown category correctly', () {
      expect(unknownCategory.isUnknown, isTrue);
      expect(testCategory.isUnknown, isFalse);
    });
  });

  group('PantryCategory List Extension Tests', () {
    late List<PantryCategory> testCategories;

    setUp(() {
      testCategories = [
        PantryCategory(id: 1, name: 'Fruits', description: 'Fresh fruits'),
        PantryCategory(id: 2, name: 'Vegetables', description: 'Fresh vegetables'),
        PantryCategory(id: 3, name: 'Dairy', description: 'Milk products'),
      ];
    });

    test('findByLabel returns correct category', () {
      final result = testCategories.findByLabel('Dairy');
      expect(result, isNotNull);
      expect(result!.name, equals('Dairy'));
    });

    test('findByLabel returns null for non-existent category', () {
      final result = testCategories.findByLabel('NonExistent');
      expect(result, isNull);
    });

    test('findByLabelOrUnknown returns unknown for non-existent category', () {
      final result = testCategories.findByLabelOrUnknown('NonExistent');
      expect(result.isUnknown, isTrue);
    });

    test('names returns list of category names', () {
      final names = testCategories.names;
      expect(names, equals(['Fruits', 'Vegetables', 'Dairy']));
    });

    test('searchCategories finds categories by name and description', () {
      final results = testCategories.searchCategories('fresh');
      expect(results.length, equals(2)); // Fruits and Vegetables have "fresh" in description
    });
  });
}
