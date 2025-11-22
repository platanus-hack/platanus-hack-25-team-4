import 'dart:convert';

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
    if (baseUrl == null || token == null) {
      // Nothing to send; treat as success to avoid backoff loops.
      return Future.value(true);
    }

    if (!await Geolocator.isLocationServiceEnabled()) {
      return Future.value(true);
    }

    final permission = await Geolocator.checkPermission();
    if (permission != LocationPermission.always) {
      return Future.value(true);
    }

    Position position;
    try {
      position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
    } catch (_) {
      // Let the system retry later.
      return Future.value(false);
    }

    final uri = Uri.parse(baseUrl).resolve('/ubicaciones');
    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'lat': position.latitude,
        'lng': position.longitude,
        'email': email,
        'recordedAt': DateTime.now().toUtc().toIso8601String(),
      }),
    );

    return response.statusCode >= 200 && response.statusCode < 300;
  });
}

class LocationPermissionService {
  Future<bool> ensureBackgroundPermission() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      return false;
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      return false;
    }
    if (permission == LocationPermission.whileInUse) {
      permission = await Geolocator.requestPermission();
    }
    return permission == LocationPermission.always;
  }
}

class LocationReportingScheduler {
  LocationReportingScheduler({required this.baseUrl, required this.mockAuth});

  final String baseUrl;
  final bool mockAuth;
  static bool _initialized = false;

  Future<void> initialize() async {
    if (mockAuth || baseUrl.isEmpty) return;
    if (!_initialized) {
      await Workmanager().initialize(locationCallbackDispatcher);
      _initialized = true;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_baseUrlKey, baseUrl);
  }

  Future<int> loadIntervalMinutes() => _loadIntervalMinutes();

  Future<bool> scheduleReporting(
    AuthSession session, {
    int? intervalMinutes,
  }) async {
    if (mockAuth || baseUrl.isEmpty) return false;

    final permissionGranted = await LocationPermissionService()
        .ensureBackgroundPermission();
    if (!permissionGranted) return false;

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
    return true;
  }

  Future<void> cancel() async {
    await Workmanager().cancelByUniqueName(locationTaskName);
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
