import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../lib/utils/expiration_utils.dart';

void main() {
  group('ExpirationUtils Tests', () {
    
    group('daysUntilExpiration', () {
      testWidgets('should return null for null expiration date', (WidgetTester tester) async {
        final result = ExpirationUtils.daysUntilExpiration(null);
        expect(result, isNull);
      });

      testWidgets('should return 0 for item expiring today', (WidgetTester tester) async {
        final today = DateTime.now();
        final todayNormalized = DateTime(today.year, today.month, today.day);
        
        final result = ExpirationUtils.daysUntilExpiration(todayNormalized);
        expect(result, equals(0));
      });

      testWidgets('should return positive days for future expiration', (WidgetTester tester) async {
        final futureDate = DateTime.now().add(const Duration(days: 5));
        
        final result = ExpirationUtils.daysUntilExpiration(futureDate);
        expect(result, equals(5));
      });

      testWidgets('should return negative days for past expiration', (WidgetTester tester) async {
        final pastDate = DateTime.now().subtract(const Duration(days: 3));
        
        final result = ExpirationUtils.daysUntilExpiration(pastDate);
        expect(result, equals(-3));
      });

      testWidgets('should handle time components correctly (normalize to day)', (WidgetTester tester) async {
        final now = DateTime.now();
        final tomorrow = DateTime(now.year, now.month, now.day + 1, 23, 59, 59);
        
        final result = ExpirationUtils.daysUntilExpiration(tomorrow);
        expect(result, equals(1));
      });
    });

    group('getExpirationUrgency', () {
      testWidgets('should return "unknown" for null expiration date', (WidgetTester tester) async {
        final result = ExpirationUtils.getExpirationUrgency(null);
        expect(result, equals('unknown'));
      });

      testWidgets('should return "expired" for past dates', (WidgetTester tester) async {
        final pastDate = DateTime.now().subtract(const Duration(days: 1));
        
        final result = ExpirationUtils.getExpirationUrgency(pastDate);
        expect(result, equals('expired'));
      });

      testWidgets('should return "critical" for today', (WidgetTester tester) async {
        final today = DateTime.now();
        
        final result = ExpirationUtils.getExpirationUrgency(today);
        expect(result, equals('critical'));
      });

      testWidgets('should return "warning" for 1 day from now', (WidgetTester tester) async {
        final tomorrow = DateTime.now().add(const Duration(days: 1));
        
        final result = ExpirationUtils.getExpirationUrgency(tomorrow);
        expect(result, equals('warning'));
      });

      testWidgets('should return "warning" for 3 days from now', (WidgetTester tester) async {
        final threeDays = DateTime.now().add(const Duration(days: 3));
        
        final result = ExpirationUtils.getExpirationUrgency(threeDays);
        expect(result, equals('warning'));
      });

      testWidgets('should return "normal" for more than 3 days from now', (WidgetTester tester) async {
        final fourDays = DateTime.now().add(const Duration(days: 4));
        
        final result = ExpirationUtils.getExpirationUrgency(fourDays);
        expect(result, equals('normal'));
      });
    });

    group('getUrgencyColor', () {
      testWidgets('should return red for expired', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyColor('expired');
        expect(result, equals(const Color(0xFFFF4444)));
      });

      testWidgets('should return orange for critical', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyColor('critical');
        expect(result, equals(const Color(0xFFFF8800)));
      });

      testWidgets('should return yellow for warning', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyColor('warning');
        expect(result, equals(const Color(0xFFFFD700)));
      });

      testWidgets('should return green for normal', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyColor('normal');
        expect(result, equals(const Color(0xFF4CAF50)));
      });

      testWidgets('should return grey for unknown', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyColor('unknown');
        expect(result, equals(const Color(0xFF9E9E9E)));
      });

      testWidgets('should return grey for invalid urgency', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyColor('invalid');
        expect(result, equals(const Color(0xFF9E9E9E)));
      });
    });

    group('getUrgencyTextColor', () {
      testWidgets('should return black for warning (yellow background)', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyTextColor('warning');
        expect(result, equals(const Color(0xFF000000)));
      });

      testWidgets('should return white for expired', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyTextColor('expired');
        expect(result, equals(const Color(0xFFFFFFFF)));
      });

      testWidgets('should return white for critical', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyTextColor('critical');
        expect(result, equals(const Color(0xFFFFFFFF)));
      });

      testWidgets('should return white for normal', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyTextColor('normal');
        expect(result, equals(const Color(0xFFFFFFFF)));
      });

      testWidgets('should return white for unknown', (WidgetTester tester) async {
        final result = ExpirationUtils.getUrgencyTextColor('unknown');
        expect(result, equals(const Color(0xFFFFFFFF)));
      });
    });

    group('getExpirationDisplayText', () {
      testWidgets('should return "No date" for null expiration', (WidgetTester tester) async {
        final result = ExpirationUtils.getExpirationDisplayText(null);
        expect(result, equals('No date'));
      });

      testWidgets('should return "EXPIRED" for past dates', (WidgetTester tester) async {
        final pastDate = DateTime.now().subtract(const Duration(days: 1));
        
        final result = ExpirationUtils.getExpirationDisplayText(pastDate);
        expect(result, equals('EXPIRED'));
      });

      testWidgets('should return "TODAY" for today', (WidgetTester tester) async {
        final today = DateTime.now();
        
        final result = ExpirationUtils.getExpirationDisplayText(today);
        expect(result, equals('TODAY'));
      });

      testWidgets('should return "Xd left" for future dates', (WidgetTester tester) async {
        final futureDate = DateTime.now().add(const Duration(days: 5));
        
        final result = ExpirationUtils.getExpirationDisplayText(futureDate);
        expect(result, equals('5d left'));
      });
    });

    group('getExpirationInfo', () {
      testWidgets('should return complete info for null expiration', (WidgetTester tester) async {
        final result = ExpirationUtils.getExpirationInfo(null);
        
        expect(result.urgency, equals('unknown'));
        expect(result.daysUntilExpiration, isNull);
        expect(result.displayText, equals('No date'));
        expect(result.backgroundColor, equals(const Color(0xFF9E9E9E)));
        expect(result.textColor, equals(const Color(0xFFFFFFFF)));
      });

      testWidgets('should return complete info for expired item', (WidgetTester tester) async {
        final pastDate = DateTime.now().subtract(const Duration(days: 2));
        final result = ExpirationUtils.getExpirationInfo(pastDate);
        
        expect(result.urgency, equals('expired'));
        expect(result.daysUntilExpiration, equals(-2));
        expect(result.displayText, equals('EXPIRED'));
        expect(result.backgroundColor, equals(const Color(0xFFFF4444)));
        expect(result.textColor, equals(const Color(0xFFFFFFFF)));
      });

      testWidgets('should return complete info for warning item', (WidgetTester tester) async {
        final warningDate = DateTime.now().add(const Duration(days: 2));
        final result = ExpirationUtils.getExpirationInfo(warningDate);
        
        expect(result.urgency, equals('warning'));
        expect(result.daysUntilExpiration, equals(2));
        expect(result.displayText, equals('2d left'));
        expect(result.backgroundColor, equals(const Color(0xFFFFD700)));
        expect(result.textColor, equals(const Color(0xFF000000)));
      });
    });

    group('Boolean convenience methods', () {
      testWidgets('isExpired should return true for past dates', (WidgetTester tester) async {
        final pastDate = DateTime.now().subtract(const Duration(days: 1));
        expect(ExpirationUtils.isExpired(pastDate), isTrue);
        expect(ExpirationUtils.isExpired(null), isFalse);
        expect(ExpirationUtils.isExpired(DateTime.now()), isFalse);
      });

      testWidgets('expiresToday should return true for today only', (WidgetTester tester) async {
        final today = DateTime.now();
        final tomorrow = DateTime.now().add(const Duration(days: 1));
        final yesterday = DateTime.now().subtract(const Duration(days: 1));
        
        expect(ExpirationUtils.expiresToday(today), isTrue);
        expect(ExpirationUtils.expiresToday(tomorrow), isFalse);
        expect(ExpirationUtils.expiresToday(yesterday), isFalse);
        expect(ExpirationUtils.expiresToday(null), isFalse);
      });

      testWidgets('expiresWithinWarningPeriod should return true for 1-3 days', (WidgetTester tester) async {
        expect(ExpirationUtils.expiresWithinWarningPeriod(
            DateTime.now().add(const Duration(days: 1))), isTrue);
        expect(ExpirationUtils.expiresWithinWarningPeriod(
            DateTime.now().add(const Duration(days: 3))), isTrue);
        expect(ExpirationUtils.expiresWithinWarningPeriod(
            DateTime.now().add(const Duration(days: 4))), isFalse);
        expect(ExpirationUtils.expiresWithinWarningPeriod(DateTime.now()), isFalse);
        expect(ExpirationUtils.expiresWithinWarningPeriod(null), isFalse);
      });

      testWidgets('isInNormalRange should return true for >3 days', (WidgetTester tester) async {
        expect(ExpirationUtils.isInNormalRange(
            DateTime.now().add(const Duration(days: 4))), isTrue);
        expect(ExpirationUtils.isInNormalRange(
            DateTime.now().add(const Duration(days: 30))), isTrue);
        expect(ExpirationUtils.isInNormalRange(
            DateTime.now().add(const Duration(days: 3))), isFalse);
        expect(ExpirationUtils.isInNormalRange(DateTime.now()), isFalse);
        expect(ExpirationUtils.isInNormalRange(null), isFalse);
      });
    });

    group('Edge cases and boundary conditions', () {
      testWidgets('should handle leap year dates correctly', (WidgetTester tester) async {
        final leapDay = DateTime(2024, 2, 29);
        final result = ExpirationUtils.daysUntilExpiration(leapDay);
        expect(result, isA<int>());
      });

      testWidgets('should handle year boundaries correctly', (WidgetTester tester) async {
        final now = DateTime.now();
        final nextYear = DateTime(now.year + 1, 1, 1);
        final result = ExpirationUtils.daysUntilExpiration(nextYear);
        expect(result, isA<int>());
        expect(result! > 0, isTrue);
      });

      testWidgets('should handle very far future dates', (WidgetTester tester) async {
        final farFuture = DateTime.now().add(const Duration(days: 10000));
        final result = ExpirationUtils.getExpirationUrgency(farFuture);
        expect(result, equals('normal'));
      });

      testWidgets('should handle very old dates', (WidgetTester tester) async {
        final veryOld = DateTime.now().subtract(const Duration(days: 10000));
        final result = ExpirationUtils.getExpirationUrgency(veryOld);
        expect(result, equals('expired'));
      });
    });

    group('ExpirationInfo equality and toString', () {
      testWidgets('should implement equality correctly', (WidgetTester tester) async {
        final info1 = ExpirationUtils.getExpirationInfo(
            DateTime.now().add(const Duration(days: 5)));
        final info2 = ExpirationUtils.getExpirationInfo(
            DateTime.now().add(const Duration(days: 5)));
        
        expect(info1, equals(info2));
        expect(info1.hashCode, equals(info2.hashCode));
      });

      testWidgets('should implement toString correctly', (WidgetTester tester) async {
        final info = ExpirationUtils.getExpirationInfo(
            DateTime.now().add(const Duration(days: 5)));
        
        final stringRep = info.toString();
        expect(stringRep, contains('ExpirationInfo'));
        expect(stringRep, contains('urgency: normal'));
        expect(stringRep, contains('daysUntilExpiration: 5'));
        expect(stringRep, contains('displayText: 5d left'));
      });
    });
  });
}
