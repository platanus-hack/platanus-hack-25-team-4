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
  LocationPermissionState _locationStatus = LocationPermissionState.denied;
  bool _checkingLocationPermission = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (_session != null) {
      _loadProfile(_session!);
    }
  }

  void _handleLogin(AuthSession session) {
    setState(() {
      _session = session;
      _profile = null;
      _profileError = null;
      _locationStatus = LocationPermissionState.denied;
      _checkingLocationPermission = false;
    });
    _loadProfile(session);
  }

  void _handleProfileCompleted(UserProfile profile) {
    setState(() {
      _profile = profile.copyWith(profileCompleted: true);
      _profileError = null;
    });
    final session = _session;
    if (session != null) {
      _startLocationReporting(session);
    }
  }

  Future<void> _handleLogout() async {
    await widget.authRepository.logout();
    await widget.locationScheduler.cancel();
    setState(() {
      _session = null;
      _profile = null;
      _profileError = null;
      _loadingProfile = false;
      _locationStatus = LocationPermissionState.denied;
      _checkingLocationPermission = false;
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
    setState(() {
      _checkingLocationPermission = true;
    });
    try {
      if (kIsWeb) {
        _maybeShowWebLimitation();
      } else {
        final currentPermission = await Geolocator.checkPermission();
        if (currentPermission != LocationPermission.always) {
          final proceed = await _showBackgroundDisclosure();
          if (!proceed) {
            setState(() {
              _locationStatus = LocationPermissionState.denied;
            });
            await _handleLocationPermissionStatus(
              LocationPermissionState.denied,
            );
            return;
          }
        }
      }

      final permissionStatus = await widget.locationScheduler.scheduleReporting(
        session,
      );
      if (!mounted) return;
      setState(() {
        _locationStatus = permissionStatus;
      });
      await _handleLocationPermissionStatus(permissionStatus);
    } finally {
      if (mounted) {
        setState(() {
          _checkingLocationPermission = false;
        });
      }
    }
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
    setState(() {
      _checkingLocationPermission = true;
    });
    try {
      final status = await _currentPermissionStatus();
      if (!mounted) return;
      if (status == LocationPermissionState.granted) {
        final session = _session;
        if (session != null) {
          final refreshedStatus = await widget.locationScheduler
              .scheduleReporting(session);
          if (mounted) {
            setState(() {
              _locationStatus = refreshedStatus;
            });
          }
        } else {
          setState(() {
            _locationStatus = status;
          });
        }
      } else {
        setState(() {
          _locationStatus = status;
        });
        await _handleLocationPermissionStatus(status);
      }
    } finally {
      if (!mounted) return;
      setState(() {
        _checkingLocationPermission = false;
      });
    }
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
    if (!mounted) return;
    if (_locationStatus != status) {
      setState(() {
        _locationStatus = status;
      });
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
      // Start location reporting only after profile is loaded and completed.
      if (_profile?.profileCompleted == true) {
        await _startLocationReporting(session);
      }
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
    if (_checkingLocationPermission) {
      return const _ProfileGateLoading();
    }
    if (_locationStatus != LocationPermissionState.granted) {
      return LocationPermissionRequiredPage(
        status: _locationStatus,
        onRequestPermission: () {
          final session = _session;
          if (session != null) {
            _startLocationReporting(session);
          }
        },
        onOpenSettings: widget.locationScheduler.openSystemSettings,
        busy: _checkingLocationPermission,
      );
    }
    return AuthenticatedShell(
      session: session,
      baseUrl: widget.config.baseUrl,
      mockApi: widget.config.mockAuth,
      onLogout: _handleLogout,
    );
  }
}

class LocationPermissionRequiredPage extends StatelessWidget {
  const LocationPermissionRequiredPage({
    required this.status,
    required this.onRequestPermission,
    required this.onOpenSettings,
    this.busy = false,
  });

  final LocationPermissionState status;
  final VoidCallback onRequestPermission;
  final Future<void> Function() onOpenSettings;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final showSettings =
        status == LocationPermissionState.deniedForever ||
        status == LocationPermissionState.serviceDisabled;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(
                Icons.location_disabled_outlined,
                size: 72,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(height: 24),
              Text(
                'Activa la ubicación siempre',
                style: theme.textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Text(
                _message,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge,
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: busy ? null : onRequestPermission,
                icon: busy
                    ? const SizedBox(
                        height: 16,
                        width: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.gps_fixed),
                label: Text(
                  busy ? 'Solicitando permiso...' : 'Activar ubicación',
                ),
              ),
              if (showSettings) ...[
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: busy ? null : () => onOpenSettings(),
                  icon: const Icon(Icons.settings),
                  label: const Text('Abrir ajustes del sistema'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  String get _message {
    switch (status) {
      case LocationPermissionState.denied:
        return 'Necesitamos permiso de ubicación siempre para protegerte y enviar tu posición en segundo plano.';
      case LocationPermissionState.deniedForever:
        return 'Habilita la ubicación siempre en los ajustes del sistema para usar la app.';
      case LocationPermissionState.serviceDisabled:
        return 'Enciende los servicios de ubicación del dispositivo para continuar.';
      case LocationPermissionState.granted:
        return '';
    }
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
