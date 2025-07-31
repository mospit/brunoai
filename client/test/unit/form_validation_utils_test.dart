import 'package:flutter_test/flutter_test.dart';

import '../../lib/utils/form_validation_utils.dart';

void main() {
    group('FormValidationUtils Tests', () {

      group('validateRequired', () {
        test('should validate that a required field is not empty', () {
          expect(FormValidationUtils.validateRequired(null, 'field'), 'Please enter field');
          expect(FormValidationUtils.validateRequired('', 'field'), 'Please enter field');
          expect(FormValidationUtils.validateRequired('  ', 'field'), 'Please enter field');
          expect(FormValidationUtils.validateRequired('valid', 'field'), isNull);
        });
      });

      group('validateQuantity', () {
        test('should validate that quantity is a positive number', () {
          expect(FormValidationUtils.validateQuantity(null), 'Please enter quantity');
          expect(FormValidationUtils.validateQuantity(''), 'Please enter quantity');
          expect(FormValidationUtils.validateQuantity('abc'), 'Please enter a valid number');
          expect(FormValidationUtils.validateQuantity('-10'), 'Quantity must be greater than 0');
          expect(FormValidationUtils.validateQuantity('0'), 'Quantity must be greater than 0');
          expect(FormValidationUtils.validateQuantity('2.5'), isNull);
        });
      });

      group('validateUnit', () {
        test('should validate that unit field is not empty', () {
          expect(FormValidationUtils.validateUnit(null), 'Please enter unit');
          expect(FormValidationUtils.validateUnit(''), 'Please enter unit');
          expect(FormValidationUtils.validateUnit('  '), 'Please enter unit');
          expect(FormValidationUtils.validateUnit('kg'), isNull);
        });
      });

      group('validateItemName', () {
        test('should validate that item name is not empty', () {
          expect(FormValidationUtils.validateItemName(null), 'Please enter item name');
          expect(FormValidationUtils.validateItemName(''), 'Please enter item name');
          expect(FormValidationUtils.validateItemName('  '), 'Please enter item name');
          expect(FormValidationUtils.validateItemName('Apples'), isNull);
        });
      });

      group('validateCategory', () {
        test('should validate that category is valid', () {
          expect(FormValidationUtils.validateCategory(null), isNull); // Optional
          expect(FormValidationUtils.validateCategory(''), isNull);    // Optional
          expect(FormValidationUtils.validateCategory('  '), isNull); // Optional
          expect(FormValidationUtils.validateCategory('f'), 'Category must be at least 2 characters');
          expect(FormValidationUtils.validateCategory('Fruit'), isNull);
        });
      });

      group('validateExpirationDate', () {
        test('should validate that expiration date is not too far in the past', () {
          expect(FormValidationUtils.validateExpirationDate(null), isNull); // Optional
          expect(
            FormValidationUtils.validateExpirationDate(DateTime.now().subtract(const Duration(days: 366))),
            'Expiration date cannot be more than 1 year in the past',
          );
          expect(
            FormValidationUtils.validateExpirationDate(DateTime.now().subtract(const Duration(days: 364))),
            isNull,
          );
        });
      });

      group('validatePantryItem', () {
        test('should validate all fields of a pantry item', () {
          final result = FormValidationUtils.validatePantryItem(
            name: null,
            quantity: '2',
            unit: '',
            category: 'f',
            expirationDate: DateTime.now().subtract(const Duration(days: 400)),
          );

          expect(result['name'], 'Please enter item name');
          expect(result['unit'], 'Please enter unit');
          expect(result['category'], 'Category must be at least 2 characters');
          expect(result['expirationDate'], 'Expiration date cannot be more than 1 year in the past');
        });
      });

      group('isValidPantryItem', () {
        test('should return true when all validations are passing', () {
          final result = FormValidationUtils.isValidPantryItem(
            name: 'Apple',
            quantity: '2',
            unit: 'kg',
            category: 'Fruit',
            expirationDate: DateTime.now().add(const Duration(days: 10)),
          );

          expect(result, isTrue);
        });

        test('should return false when any validation is failing', () {
          final result = FormValidationUtils.isValidPantryItem(
            name: 'Apple',
            quantity: '-2',
            unit: '',
            category: 'f',
            expirationDate: DateTime.now().subtract(const Duration(days: 400)),
          );

          expect(result, isFalse);
        });
      });

  });
}

