import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/config/app_config.dart';
import 'core/storage/credentials_storage.dart';
import 'core/theme/app_theme.dart';
import 'core/background/location_reporting_worker.dart';
import 'features/app/presentation/authenticated_shell.dart';
import 'features/auth/data/auth_api_client.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/domain/auth_session.dart';
import 'features/auth/presentation/login_page.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final config = await AppConfig.load();
  final authRepository = AuthRepository(
    apiClient: AuthApiClient(
      baseUrl: config.baseUrl,
      mockAuth: config.mockAuth,
    ),
    storage: CredentialsStorage(),
  );
  final initialSession = await authRepository.loadSavedSession();
  final locationScheduler = LocationReportingScheduler(
    baseUrl: config.baseUrl,
    mockAuth: config.mockAuth,
  );
  await locationScheduler.initialize();

  runApp(
    MyApp(
      config: config,
      authRepository: authRepository,
      initialSession: initialSession,
      locationScheduler: locationScheduler,
    ),
  );
}

class MyApp extends StatefulWidget {
  const MyApp({
    super.key,
    required this.config,
    required this.authRepository,
    required this.locationScheduler,
    this.initialSession,
  });

  final AppConfig config;
  final AuthRepository authRepository;
  final LocationReportingScheduler locationScheduler;
  final AuthSession? initialSession;

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late AuthSession? _session = widget.initialSession;

  @override
  void initState() {
    super.initState();
    if (_session != null) {
      _startLocationReporting(_session!);
    }
  }

  void _handleLogin(AuthSession session) {
    setState(() {
      _session = session;
    });
    _startLocationReporting(session);
  }

  Future<void> _handleLogout() async {
    await widget.authRepository.logout();
    await widget.locationScheduler.cancel();
    setState(() {
      _session = null;
    });
  }

  Future<void> _startLocationReporting(AuthSession session) async {
    await widget.locationScheduler.scheduleReporting(session);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Circles',
      locale: const Locale('es'),
      supportedLocales: const [Locale('es')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: appTheme,
      home: _session == null
          ? LoginPage(
              authRepository: widget.authRepository,
              onLoggedIn: _handleLogin,
            )
          : AuthenticatedShell(
              session: _session!,
              onLogout: _handleLogout,
            ),
    );
  }
}
