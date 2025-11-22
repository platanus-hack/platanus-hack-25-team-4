import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:geolocator/geolocator.dart';

import 'core/config/app_config.dart';
import 'core/storage/credentials_storage.dart';
import 'core/theme/app_theme.dart';
import 'core/background/location_reporting_worker.dart';
import 'features/app/presentation/authenticated_shell.dart';
import 'features/auth/data/auth_api_client.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/domain/auth_session.dart';
import 'features/auth/presentation/login_page.dart';
import 'features/profile/data/profile_api_client.dart';
import 'features/profile/data/profile_repository.dart';
import 'features/profile/domain/user_profile.dart';
import 'features/profile/presentation/profile_wizard_page.dart';

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
  final profileRepository = ProfileRepository(
    apiClient: ProfileApiClient(
      baseUrl: config.baseUrl,
      mockAuth: config.mockAuth,
    ),
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
      profileRepository: profileRepository,
    ),
  );
}

class MyApp extends StatefulWidget {
  const MyApp({
    super.key,
    required this.config,
    required this.authRepository,
    required this.locationScheduler,
    required this.profileRepository,
    this.initialSession,
  });

  final AppConfig config;
  final AuthRepository authRepository;
  final ProfileRepository profileRepository;
  final LocationReportingScheduler locationScheduler;
  final AuthSession? initialSession;

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> with WidgetsBindingObserver {
  late AuthSession? _session = widget.initialSession;
  UserProfile? _profile;
  bool _loadingProfile = false;
  String? _profileError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (_session != null) {
      _startLocationReporting(_session!);
      _loadProfile(_session!);
    }
  }

  void _handleLogin(AuthSession session) {
    setState(() {
      _session = session;
      _profile = null;
      _profileError = null;
    });
    _startLocationReporting(session);
    _loadProfile(session);
  }

  void _handleProfileCompleted(UserProfile profile) {
    setState(() {
      _profile = profile.copyWith(profileCompleted: true);
      _profileError = null;
    });
  }

  Future<void> _handleLogout() async {
    await widget.authRepository.logout();
    await widget.locationScheduler.cancel();
    setState(() {
      _session = null;
      _profile = null;
      _profileError = null;
      _loadingProfile = false;
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    if (state == AppLifecycleState.resumed && _session != null) {
      _recheckBackgroundPermission();
    }
  }

  Future<void> _startLocationReporting(AuthSession session) async {
    if (kIsWeb) {
      _maybeShowWebLimitation();
    } else {
      final currentPermission = await Geolocator.checkPermission();
      if (currentPermission != LocationPermission.always) {
        final proceed = await _showBackgroundDisclosure();
        if (!proceed) {
          await _handleLocationPermissionStatus(LocationPermissionState.denied);
          return;
        }
      }
    }

    final permissionStatus = await widget.locationScheduler.scheduleReporting(
      session,
    );
    if (!mounted) return;
    await _handleLocationPermissionStatus(permissionStatus);
  }

  void _maybeShowWebLimitation() {
    final messenger = ScaffoldMessenger.maybeOf(context);
    messenger?.showSnackBar(
      const SnackBar(
        content: Text(
          'En la web no podemos rastrear en segundo plano. Usa la app móvil '
          'para enviar ubicación continua.',
        ),
        duration: Duration(seconds: 6),
      ),
    );
  }

  Future<void> _recheckBackgroundPermission() async {
    final status = await _currentPermissionStatus();
    if (!mounted) return;
    if (status == LocationPermissionState.granted) {
      final session = _session;
      if (session != null) {
        await widget.locationScheduler.scheduleReporting(session);
      }
      return;
    }
    await _handleLocationPermissionStatus(status);
  }

  Future<LocationPermissionState> _currentPermissionStatus() async {
    if (kIsWeb) return LocationPermissionState.granted;
    final enabled = await Geolocator.isLocationServiceEnabled();
    if (!enabled) return LocationPermissionState.serviceDisabled;
    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.always) {
      return LocationPermissionState.granted;
    }
    if (permission == LocationPermission.deniedForever) {
      return LocationPermissionState.deniedForever;
    }
    return LocationPermissionState.denied;
  }

  Future<bool> _showBackgroundDisclosure() async {
    return await showDialog<bool>(
          context: context,
          barrierDismissible: false,
          builder: (ctx) {
            return AlertDialog(
              title: const Text('Activa ubicación siempre'),
              content: const Text(
                'Para mantenerte protegido y enviar tu ubicación aunque la app '
                'esté cerrada, necesitamos permiso de ubicación en segundo '
                'plano. Sin esto, la app no puede funcionar correctamente.',
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(ctx).pop(false),
                  child: const Text('Cancelar'),
                ),
                FilledButton(
                  onPressed: () => Navigator.of(ctx).pop(true),
                  child: const Text('Continuar'),
                ),
              ],
            );
          },
        ) ??
        false;
  }

  Future<void> _handleLocationPermissionStatus(
    LocationPermissionState status,
  ) async {
    if (!mounted || status == LocationPermissionState.granted) return;

    String message;
    switch (status) {
      case LocationPermissionState.denied:
        message =
            'Activa la ubicación siempre para seguir enviando ubicaciones incluso en segundo plano.';
        break;
      case LocationPermissionState.deniedForever:
        message =
            'Debes habilitar la ubicación siempre desde ajustes para que la app funcione.';
        break;
      case LocationPermissionState.serviceDisabled:
        message = 'Activa los servicios de ubicación para continuar.';
        break;
      case LocationPermissionState.granted:
        return;
    }

    final shouldOpenSettings = await showDialog<bool>(
          context: context,
          barrierDismissible: false,
          builder: (ctx) {
            return AlertDialog(
              title: const Text('Ubicación requerida'),
              content: Text(message),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(ctx).pop(false),
                  child: const Text('Ahora no'),
                ),
                FilledButton.icon(
                  onPressed: () => Navigator.of(ctx).pop(true),
                  icon: const Icon(Icons.settings),
                  label: const Text('Abrir ajustes'),
                ),
              ],
            );
          },
        ) ??
        false;

    if (shouldOpenSettings) {
      await widget.locationScheduler.openSystemSettings();
    }
  }

  Future<void> _loadProfile(AuthSession session) async {
    setState(() {
      _loadingProfile = true;
      _profileError = null;
      _profile = null;
    });
    try {
      final profile = await widget.profileRepository.fetchCurrentUser(session);
      if (!mounted) return;
      setState(() {
        _profile = profile.copyWith(email: session.email);
        _loadingProfile = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _profileError = e.toString().replaceFirst('ProfileException: ', '');
        _loadingProfile = false;
        _profile = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final home = _session == null
        ? LoginPage(
            authRepository: widget.authRepository,
            onLoggedIn: _handleLogin,
          )
        : _buildProfileAwareHome();

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
      home: home,
    );
  }

  Widget _buildProfileAwareHome() {
    final session = _session;
    if (session == null) return const SizedBox.shrink();

    if (_loadingProfile) {
      return const _ProfileGateLoading();
    }
    if (_profileError != null) {
      return _ProfileGateError(
        message: _profileError!,
        onRetry: () => _loadProfile(session),
        onLogout: _handleLogout,
      );
    }
    if (_profile == null) {
      return const _ProfileGateLoading();
    }
    if (!_profile!.profileCompleted) {
      return ProfileWizardPage(
        session: session,
        repository: widget.profileRepository,
        initialBio: _profile!.bio,
        initialInterests: _profile!.interests,
        onCompleted: _handleProfileCompleted,
        onLogout: _handleLogout,
      );
    }
    return AuthenticatedShell(session: session, onLogout: _handleLogout);
  }
}

class _ProfileGateLoading extends StatelessWidget {
  const _ProfileGateLoading();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}

class _ProfileGateError extends StatelessWidget {
  const _ProfileGateError({
    required this.message,
    required this.onRetry,
    required this.onLogout,
  });

  final String message;
  final VoidCallback onRetry;
  final Future<void> Function() onLogout;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tu perfil'),
        actions: [
          IconButton(
            onPressed: () {
              onLogout();
            },
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'No pudimos cargar tu perfil',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(
                message,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.error,
                ),
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
