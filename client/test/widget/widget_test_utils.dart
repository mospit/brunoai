import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';
import 'package:mockito/annotations.dart';

// Import your BLoCs and services
import '../../lib/bloc/auth/auth_bloc.dart';
import '../../lib/bloc/auth/auth_event.dart';
import '../../lib/bloc/auth/auth_state.dart';
import '../../lib/bloc/household/household_bloc.dart';
import '../../lib/bloc/household/household_state.dart';
import '../../lib/services/auth_service.dart';
import '../../lib/services/household_service.dart';
import '../../lib/models/user.dart';
import '../../lib/models/household.dart';

// Mock classes for navigation and services
class MockNavigatorObserver extends Mock implements NavigatorObserver {}
class MockAuthService extends Mock implements AuthService {}
class MockHouseholdService extends Mock implements HouseholdService {}

// Mock BLoCs
class MockAuthBloc extends Mock implements AuthBloc {}
class MockHouseholdBloc extends Mock implements HouseholdBloc {}

/// Utility class for widget testing
class WidgetTestUtils {
  /// Default test user
  static final User testUser = User(
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    firebaseUid: 'firebase-uid-123',
    isActive: true,
    isVerified: true,
    createdAt: DateTime.now(),
  );

  /// Default test household
  static final Household testHousehold = Household(
    id: '1',
    name: 'Test Household',
    description: 'A test household',
    createdBy: '1',
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
    members: [],
  );

  /// Mock Navigator Observer for tracking navigation events
  static MockNavigatorObserver createMockNavigator() {
    return MockNavigatorObserver();
  }

  /// Create a mock AuthBloc with default authenticated state
  static MockAuthBloc createMockAuthBloc({AuthState? initialState}) {
    final mockBloc = MockAuthBloc();
    final defaultState = initialState ?? AuthAuthenticated(testUser);
    when(mockBloc.state).thenReturn(defaultState);
    when(mockBloc.stream).thenAnswer((_) => Stream.value(defaultState));
    // Mock the add method to avoid argument type issues
    // Remove specific argument matching to avoid type issues
    return mockBloc;
  }

  /// Create a mock HouseholdBloc with default loaded state
  static MockHouseholdBloc createMockHouseholdBloc({HouseholdState? initialState}) {
    final mockBloc = MockHouseholdBloc();
    final defaultState = initialState ?? HouseholdLoaded(
      households: [testHousehold],
      selectedHousehold: testHousehold,
    );
    when(mockBloc.state).thenReturn(defaultState);
    when(mockBloc.households).thenReturn([testHousehold]);
    when(mockBloc.selectedHousehold).thenReturn(testHousehold);
    when(mockBloc.stream).thenAnswer((_) => Stream.value(defaultState));
    return mockBloc;
  }

  /// Wrap a widget with basic testing providers (MaterialApp + BlocProviders)
  static Widget wrapWithTestingWidget(
    Widget widget, {
    MockAuthBloc? authBloc,
    MockHouseholdBloc? householdBloc,
    List<NavigatorObserver>? navigatorObservers,
    ThemeData? theme,
    Locale? locale,
    RouteSettings? initialRoute,
  }) {
    final mockAuthBloc = authBloc ?? createMockAuthBloc();
    final mockHouseholdBloc = householdBloc ?? createMockHouseholdBloc();
    final observers = navigatorObservers ?? [createMockNavigator()];

    return MaterialApp(
      theme: theme ?? ThemeData(),
      locale: locale,
      navigatorObservers: observers,
      home: MultiBlocProvider(
        providers: [
          BlocProvider<AuthBloc>.value(value: mockAuthBloc),
          BlocProvider<HouseholdBloc>.value(value: mockHouseholdBloc),
        ],
        child: widget,
      ),
    );
  }

  /// Wrap a widget with testing providers but using a custom route setup
  static Widget wrapWithTestingRouter(
    Widget widget, {
    required String initialRoute,
    required Map<String, WidgetBuilder> routes,
    MockAuthBloc? authBloc,
    MockHouseholdBloc? householdBloc,
    List<NavigatorObserver>? navigatorObservers,
    ThemeData? theme,
  }) {
    final mockAuthBloc = authBloc ?? createMockAuthBloc();
    final mockHouseholdBloc = householdBloc ?? createMockHouseholdBloc();
    final observers = navigatorObservers ?? [createMockNavigator()];

    return MultiBlocProvider(
      providers: [
        BlocProvider<AuthBloc>.value(value: mockAuthBloc),
        BlocProvider<HouseholdBloc>.value(value: mockHouseholdBloc),
      ],
      child: MaterialApp(
        theme: theme ?? ThemeData(),
        navigatorObservers: observers,
        initialRoute: initialRoute,
        routes: routes,
      ),
    );
  }

  /// Wrap a widget with minimal testing setup (just MaterialApp)
  static Widget wrapWithMaterialApp(
    Widget widget, {
    ThemeData? theme,
    List<NavigatorObserver>? navigatorObservers,
  }) {
    return MaterialApp(
      theme: theme ?? ThemeData(),
      navigatorObservers: navigatorObservers ?? [createMockNavigator()],
      home: Scaffold(body: widget),
    );
  }

  /// Create mock services for testing
  static MockAuthService createMockAuthService({
    bool isLoggedIn = true,
    User? user,
    String? token,
  }) {
    final mockService = MockAuthService();
    when(mockService.isLoggedIn()).thenAnswer((_) async => isLoggedIn);
    when(mockService.getCurrentUser()).thenAnswer((_) async => user ?? testUser);
    when(mockService.getToken()).thenAnswer((_) async => token ?? 'mock-token');
    return mockService;
  }

  static MockHouseholdService createMockHouseholdService({
    List<Household>? households,
    Household? selectedHousehold,
  }) {
    final mockService = MockHouseholdService();
    when(mockService.getUserHouseholds()).thenAnswer((_) async => households ?? [testHousehold]);
    when(mockService.getHousehold('test-id')).thenAnswer((_) async => selectedHousehold ?? testHousehold);
    return mockService;
  }

  /// Helper to pump a widget and wait for async operations
  static Future<void> pumpAndSettleWidget(
    WidgetTester tester,
    Widget widget, {
    Duration? duration,
  }) async {
    await tester.pumpWidget(widget);
    if (duration != null) {
      await tester.pumpAndSettle(duration);
    } else {
      await tester.pumpAndSettle();
    }
  }
}

