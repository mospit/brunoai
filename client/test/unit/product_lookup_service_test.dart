import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:http/http.dart' as http;
import '../../lib/services/product_lookup_service.dart';
import '../../lib/models/product.dart';

// Generate mocks
@GenerateMocks([http.Client])
import 'product_lookup_service_test.mocks.dart';

void main() {
  group('ProductLookupService', () {
    late ProductLookupService service;
    late MockClient mockClient;

    setUp(() {
      service = ProductLookupService();
      mockClient = MockClient();
    });

    group('barcode validation', () {
      test('should validate correct barcode formats', () {
        expect(service.isValidBarcode('1234567890123'), true); // EAN-13
        expect(service.isValidBarcode('12345678'), true); // EAN-8
        expect(service.isValidBarcode('123456789012'), true); // UPC-A
        expect(service.isValidBarcode('12345678901234'), true); // 14-digit
      });

      test('should reject invalid barcode formats', () {
        expect(service.isValidBarcode(''), false); // empty
        expect(service.isValidBarcode('abc123'), false); // contains letters
        expect(service.isValidBarcode('12345'), false); // too short
        expect(service.isValidBarcode('123456789012345'), false); // too long
        expect(service.isValidBarcode('12 34 56'), false); // contains spaces
      });

      test('should clean barcode properly', () {
        expect(service.cleanBarcode(' 1234567890123 '), '1234567890123');
        expect(service.cleanBarcode('12 34 56'), '123456');
        expect(service.cleanBarcode('  123  456  '), '123456');
      });
    });

    group('fallback product creation', () {
      test('should create fallback product with barcode', () {
        const barcode = '1234567890123';
        final product = service.createFallbackProduct(barcode);

        expect(product.barcode, barcode);
        expect(product.name, 'Unknown Product');
        expect(product.brand, 'Unknown Brand');
        expect(product.category, 'Other');
        expect(product.description, contains('not found'));
      });
    });

    group('Product model validation', () {
      test('should validate valid product', () {
        final product = Product(
          barcode: '1234567890123',
          name: 'Test Product',
          brand: 'Test Brand',
          category: 'Food',
        );

        expect(product.isValid, true);
        expect(product.toString(), contains('Test Product'));
      });

      test('should invalidate product without name', () {
        final product = Product(
          barcode: '1234567890123',
          brand: 'Test Brand',
          category: 'Food',
        );

        expect(product.isValid, false);
      });

      test('should invalidate product with empty name', () {
        final product = Product(
          barcode: '1234567890123',
          name: '',
          brand: 'Test Brand',
          category: 'Food',
        );

        expect(product.isValid, false);
      });
    });

    group('OpenFoodFacts JSON parsing', () {
      test('should parse valid OpenFoodFacts response', () {
        final jsonResponse = {
          'status': 1,
          'code': '1234567890123',
          'product': {
            'product_name': 'Test Product',
            'brands': 'Test Brand',
            'categories_tags': ['en:food', 'en:dairy'],
            'generic_name': 'A test product',
            'image_url': 'https://example.com/image.jpg',
            'nutriments': {'energy': 100}
          }
        };

        final product = Product.fromOpenFoodFacts(jsonResponse);

        expect(product.barcode, '1234567890123');
        expect(product.name, 'Test Product');
        expect(product.brand, 'Test Brand');
        expect(product.category, 'food');
        expect(product.description, 'A test product');
        expect(product.images, contains('https://example.com/image.jpg'));
        expect(product.nutritionInfo, isNotNull);
        expect(product.isValid, true);
      });

      test('should handle missing OpenFoodFacts product data', () {
        final jsonResponse = {
          'status': 0,
          'code': '1234567890123',
        };

        final product = Product.fromOpenFoodFacts(jsonResponse);

        expect(product.barcode, '1234567890123');
        expect(product.name, null);
        expect(product.isValid, false);
      });
    });

    group('UPC Database JSON parsing', () {
      test('should parse valid UPC Database response', () {
        final jsonResponse = {
          'ean': '1234567890123',
          'title': 'Test Product',
          'brand': 'Test Brand',
          'category': 'Food',
          'description': 'A test product',
          'images': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']
        };

        final product = Product.fromUPCDatabase(jsonResponse);

        expect(product.barcode, '1234567890123');
        expect(product.name, 'Test Product');
        expect(product.brand, 'Test Brand');
        expect(product.category, 'Food');
        expect(product.description, 'A test product');
        expect(product.images?.length, 2);
        expect(product.isValid, true);
      });
    });
  });
}
