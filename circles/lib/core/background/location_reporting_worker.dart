import 'dart:convert';

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

enum LocationPermissionState { granted, denied, deniedForever, serviceDisabled }

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

    if (baseUrl == null || baseUrl.isEmpty || token == null) {
      _logWorker('Sin backend configurado/token; se registra solo en consola.');
      return Future.value(true);
    }

    final uri = Uri.parse(baseUrl).resolve('/ubicaciones');
    http.Response response;
    try {
      response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'lat': position.latitude,
          'lng': position.longitude,
          'email': email,
          'recordedAt': now.toIso8601String(),
        }),
      );
    } catch (e) {
      _logWorker('Error al enviar ubicación: $e');
      return Future.value(true);
    }

    final ok = response.statusCode >= 200 && response.statusCode < 300;
    if (!ok) {
      _logWorker(
        'Backend respondió ${response.statusCode}: ${response.body}',
      );
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
      return upgraded == LocationPermission.deniedForever
          ? LocationPermissionState.deniedForever
          : LocationPermissionState.denied;
    }
    return permission == LocationPermission.always
        ? LocationPermissionState.granted
        : LocationPermissionState.denied;
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

  Future<LocationPermissionState> scheduleReporting(
    AuthSession session, {
    int? intervalMinutes,
  }) async {
    final permission = await LocationPermissionService()
        .ensureBackgroundPermission();
    if (permission != LocationPermissionState.granted) {
      _log('Permiso de ubicación no concedido: $permission');
      return permission;
    }

    if (kIsWeb) {
      _log(
        'Permiso concedido en web; no se agenda background, solo foreground.',
      );
      return LocationPermissionState.granted;
    }

    if (mockAuth) {
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
    if (kIsWeb || mockAuth) {
      _log('Cancelación omitida (web/mock)');
      return;
    }
    await Workmanager().cancelByUniqueName(locationTaskName);
  }

  Future<void> openSystemSettings() {
    return LocationPermissionService().openSystemSettings();
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
