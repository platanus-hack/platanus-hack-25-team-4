import 'dart:async';
import 'dart:convert';

import 'package:circles/core/auth/unauthorized_handler.dart';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:workmanager/workmanager.dart';

import '../storage/credentials_storage.dart';
import '../../features/auth/domain/auth_session.dart';

const locationTaskName = 'com.example.circles.location.periodic';
const _intervalKey = 'location_interval_minutes';
const _baseUrlKey = 'api_base_url';
const defaultLocationIntervalMinutes = 30;
const minLocationIntervalMinutes = 15;
const maxLocationIntervalMinutes = 180;
const foregroundLocationInterval = Duration(seconds: 30);

enum LocationPermissionState {
  granted,
  foregroundOnly,
  denied,
  deniedForever,
  serviceDisabled,
}

@pragma('vm:entry-point')
void locationCallbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    final shouldHandle =
        task == locationTaskName || task == Workmanager.iOSBackgroundTask;
    if (!shouldHandle) return Future.value(true);

    final prefs = await SharedPreferences.getInstance();
    final baseUrl = prefs.getString(_baseUrlKey);
    final token = prefs.getString(CredentialsStorage.tokenKey);
    final email = prefs.getString(CredentialsStorage.emailKey);

    if (!await Geolocator.isLocationServiceEnabled()) {
      _logWorker('Servicios de ubicación desactivados; se omite envío.');
      return Future.value(true);
    }

    final permission = await Geolocator.checkPermission();
    if (permission != LocationPermission.always) {
      _logWorker('Permiso de ubicación en segundo plano no concedido.');
      return Future.value(true);
    }

    Position position;
    try {
      position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
    } catch (e) {
      _logWorker('No se pudo obtener la ubicación: $e');
      // Let the system retry later.
      return Future.value(false);
    }

    final now = DateTime.now().toUtc();
    _logWorker(
      'Coordenada capturada lat=${position.latitude}, lng=${position.longitude}, at=$now, email=${email ?? 'n/a'}',
    );

    final success = await _sendPositionUpdate(
      baseUrl: baseUrl ?? '',
      token: token ?? '',
      position: position,
      log: _logWorker,
    );
    if (!success) {
      _logWorker('No se pudo enviar la ubicación en background.');
    }
    return Future.value(true);
  });
}

class LocationPermissionService {
  Future<LocationPermissionState> ensureBackgroundPermission() async {
    if (kIsWeb) {
      return (await _ensureForegroundPermission())
          ? LocationPermissionState.granted
          : LocationPermissionState.denied;
    }

    if (!await Geolocator.isLocationServiceEnabled()) {
      return LocationPermissionState.serviceDisabled;
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.deniedForever) {
      return LocationPermissionState.deniedForever;
    }
    if (permission == LocationPermission.whileInUse) {
      final upgraded = await Geolocator.requestPermission();
      if (upgraded == LocationPermission.always) {
        return LocationPermissionState.granted;
      }
      if (upgraded == LocationPermission.deniedForever) {
        return LocationPermissionState.deniedForever;
      }
      return upgraded == LocationPermission.whileInUse
          ? LocationPermissionState.foregroundOnly
          : LocationPermissionState.denied;
    }
    return permission == LocationPermission.always
        ? LocationPermissionState.granted
        : LocationPermissionState.foregroundOnly;
  }

  Future<bool> _ensureForegroundPermission() async {
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.deniedForever) {
      return false;
    }
    return permission == LocationPermission.always ||
        permission == LocationPermission.whileInUse;
  }

  Future<void> openSystemSettings() async {
    await Geolocator.openLocationSettings();
    await Geolocator.openAppSettings();
  }
}

class LocationReportingScheduler {
  LocationReportingScheduler({required this.baseUrl, required this.mockAuth});

  final String baseUrl;
  final bool mockAuth;
  static bool _initialized = false;
  bool _sendingSnapshot = false;
  Timer? _foregroundTimer;

  Future<void> initialize() async {
    if (kIsWeb || mockAuth) return;
    if (!_initialized) {
      await Workmanager().initialize(locationCallbackDispatcher);
      _initialized = true;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_baseUrlKey, baseUrl);
  }

  Future<int> loadIntervalMinutes() => _loadIntervalMinutes();

  Future<void> _startForegroundLoop(AuthSession session) async {
    await _stopForegroundLoop();
    await _sendLocationSnapshot(session);
    _foregroundTimer = Timer.periodic(
      foregroundLocationInterval,
      (_) => _sendLocationSnapshot(session),
    );
    _log(
      'Permiso de background denegado; se envía ubicación en primer plano cada '
      '${foregroundLocationInterval.inSeconds}s mientras la app esté abierta.',
    );
  }

  Future<void> _stopForegroundLoop() async {
    _foregroundTimer?.cancel();
    _foregroundTimer = null;
  }

  Future<LocationPermissionState> scheduleReporting(
    AuthSession session, {
    int? intervalMinutes,
  }) async {
    final permission = await LocationPermissionService()
        .ensureBackgroundPermission();
    if (permission == LocationPermissionState.denied ||
        permission == LocationPermissionState.deniedForever ||
        permission == LocationPermissionState.serviceDisabled) {
      await _stopForegroundLoop();
      _log('Permiso de ubicación no concedido: $permission');
      return permission;
    }

    if (permission == LocationPermissionState.foregroundOnly) {
      await _stopForegroundLoop();
      if (!kIsWeb && !mockAuth) {
        await Workmanager().cancelByUniqueName(locationTaskName);
      }
      await _startForegroundLoop(session);
      return permission;
    }

    await _stopForegroundLoop();

    if (kIsWeb) {
      await _sendLocationSnapshot(session);
      _log(
        'Permiso concedido en web; no se agenda background, solo foreground.',
      );
      return LocationPermissionState.granted;
    }

    if (mockAuth) {
      await _sendLocationSnapshot(session);
      _log('Permiso concedido en modo mock; no se agenda envío.');
      return LocationPermissionState.granted;
    }

    if (baseUrl.isEmpty) {
      _log(
        'Permiso concedido sin backend configurado; se agenda para registrar coordenadas en consola.',
      );
    }

    await initialize();

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(CredentialsStorage.tokenKey, session.token);
    await prefs.setString(CredentialsStorage.emailKey, session.email);
    final minutes = _sanitizeInterval(
      intervalMinutes ?? await _loadIntervalMinutes(),
    );
    await prefs.setInt(_intervalKey, minutes);
    await prefs.setString(_baseUrlKey, baseUrl);
    await _sendLocationSnapshot(session);

    await Workmanager().registerPeriodicTask(
      locationTaskName,
      locationTaskName,
      existingWorkPolicy: ExistingWorkPolicy.replace,
      frequency: Duration(minutes: minutes),
      initialDelay: const Duration(minutes: 1),
      inputData: {'interval': minutes},
    );
    return LocationPermissionState.granted;
  }

  Future<void> cancel() async {
    await _stopForegroundLoop();
    if (kIsWeb || mockAuth) {
      _log('Cancelación omitida (web/mock)');
      return;
    }
    await Workmanager().cancelByUniqueName(locationTaskName);
  }

  Future<void> openSystemSettings() {
    return LocationPermissionService().openSystemSettings();
  }

  Future<void> _sendLocationSnapshot(AuthSession session) async {
    if (_sendingSnapshot) return;
    _sendingSnapshot = true;
    try {
      if (!await Geolocator.isLocationServiceEnabled()) {
        _log(
          'Servicios de ubicación desactivados; no se envía ubicación inmediata.',
        );
        return;
      }
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      final granted = permission == LocationPermission.always ||
          permission == LocationPermission.whileInUse ||
          kIsWeb;
      if (!granted) {
        _log('Permiso insuficiente para envío inmediato: $permission');
        return;
      }
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
      await _sendPositionUpdate(
        baseUrl: baseUrl,
        token: session.token,
        position: position,
        log: _log,
      );
    } catch (e) {
      _log('Error al enviar ubicación inmediata: $e');
    } finally {
      _sendingSnapshot = false;
    }
  }
}

int _sanitizeInterval(int value) {
  return value
      .clamp(minLocationIntervalMinutes, maxLocationIntervalMinutes)
      .toInt();
}

Future<int> _loadIntervalMinutes() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getInt(_intervalKey) ?? defaultLocationIntervalMinutes;
}

void _log(String message) {
  // Lightweight logger for background location scheduling.
  // In production you might route this to a proper logger.
  // ignore: avoid_print
  print('[LocationScheduler] $message');
}

void _logWorker(String message) {
  // ignore: avoid_print
  print('[LocationWorker] $message');
}

Uri _buildUri(String baseUrl, String path) {
  final base = baseUrl.endsWith('/')
      ? baseUrl.substring(0, baseUrl.length - 1)
      : baseUrl;
  final cleanPath = path.startsWith('/') ? path.substring(1) : path;
  return Uri.parse('$base/$cleanPath');
}

Future<bool> _sendPositionUpdate({
  required String baseUrl,
  required String token,
  required Position position,
  required void Function(String) log,
}) async {
  if (baseUrl.isEmpty || token.isEmpty) {
    log('Sin backend configurado/token; se registra solo en consola.');
    return true;
  }

  final uri = _buildUri(baseUrl, '/users/me/position');
  try {
    final response = await http.patch(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'centerLat': position.latitude,
        'centerLon': position.longitude,
      }),
    );
    if (response.statusCode == 401) {
      await UnauthorizedHandler.handleUnauthorized();
      return false;
    }
    final ok = response.statusCode >= 200 && response.statusCode < 300;
    if (!ok) {
      log('Backend respondió ${response.statusCode}: ${response.body}');
    }
    return ok;
  } catch (e) {
    log('Error al enviar ubicación: $e');
    return false;
  }
}
