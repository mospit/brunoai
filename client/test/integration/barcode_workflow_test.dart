import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';
import '../../lib/main.dart';
import '../../lib/services/product_lookup_service.dart';
import '../../lib/services/pantry_service.dart';
import '../../lib/models/product.dart';
import '../../lib/screens/barcode_scanner_screen.dart';
import '../../lib/screens/voice_pantry_screen.dart';

class MockProductLookupService extends Mock implements ProductLookupService {}
class MockPantryService extends Mock implements PantryService {}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Barcode Scanning Workflow', () {
    testWidgets('should navigate to scanner screen and display UI',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            Provider<ProductLookupService>(
              create: (_) => ProductLookupService(),
            ),
            Provider<PantryService>(
              create: (_) => PantryService(),
            ),
          ],
          child: const MaterialApp(
            home: VoicePantryScreen(),
          ),
        ),
      );

      // Verify home screen
      expect(find.text('Voice Pantry'), findsWidgets);
      expect(find.byIcon(Icons.qr_code_scanner), findsWidgets);
      
      // Navigate to scanner
      await tester.tap(find.text('Scan Barcode'));
      await tester.pumpAndSettle();

      // Verify scanner screen
      expect(find.text('Scan Barcode'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });
  });
}

