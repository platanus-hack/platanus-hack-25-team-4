import 'package:circles/core/background/location_reporting_worker.dart';
import 'package:circles/core/config/app_config.dart';
import 'package:circles/core/storage/credentials_storage.dart';
import 'package:circles/features/auth/data/auth_api_client.dart';
import 'package:circles/features/auth/data/auth_repository.dart';
import 'package:circles/features/auth/domain/auth_session.dart';
import 'package:circles/features/profile/data/profile_api_client.dart';
import 'package:circles/features/profile/data/profile_repository.dart';
import 'package:circles/main.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Shows profile wizard when profile is incompleto', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({});

    final authRepository = AuthRepository(
      apiClient: AuthApiClient(baseUrl: '', mockAuth: true),
      storage: CredentialsStorage(),
    );
    final profileRepository = ProfileRepository(
      apiClient: ProfileApiClient(baseUrl: '', mockAuth: true),
    );
    final locationScheduler = LocationReportingScheduler(
      baseUrl: '',
      mockAuth: true,
    );

    await tester.pumpWidget(
      MyApp(
        config: AppConfig(baseUrl: '', mockAuth: true),
        authRepository: authRepository,
        locationScheduler: locationScheduler,
        profileRepository: profileRepository,
        initialSession: AuthSession(email: 'test@circles.dev', token: 't123'),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Completa tu perfil'), findsOneWidget);
    expect(find.text('Intereses'), findsOneWidget);
  });
}
