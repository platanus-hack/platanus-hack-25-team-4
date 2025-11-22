import 'package:circles/core/config/app_config.dart';
import 'package:circles/core/storage/credentials_storage.dart';
import 'package:circles/core/background/location_reporting_worker.dart';
import 'package:circles/features/auth/data/auth_api_client.dart';
import 'package:circles/features/auth/data/auth_repository.dart';
import 'package:circles/main.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Login form renders for unauthenticated users', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({});

    final authRepository = AuthRepository(
      apiClient: AuthApiClient(baseUrl: '', mockAuth: true),
      storage: CredentialsStorage(),
    );
    final locationScheduler = LocationReportingScheduler(
      baseUrl: '',
      mockAuth: true,
    );
    await tester.pumpWidget(
      MyApp(
        config: AppConfig(baseUrl: '', mockAuth: true),
        authRepository: authRepository,
        initialSession: null,
        locationScheduler: locationScheduler,
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Bienvenido a Circles'), findsOneWidget);
    expect(find.text('Correo'), findsOneWidget);
    expect(find.text('Contraseña'), findsOneWidget);
    expect(find.text('Ingresar'), findsOneWidget);
  });
}
