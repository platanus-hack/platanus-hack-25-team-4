import 'dart:convert';

import 'package:circles/core/auth/unauthorized_handler.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../domain/user_profile.dart';

class ProfileApiClient {
  ProfileApiClient({
    required this.baseUrl,
    required this.mockAuth,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final bool mockAuth;
  final http.Client _client;

  static const _headers = {'Content-Type': 'application/json'};
  static const _mockProfileKey = 'profile_mock_v1';

  Future<UserProfile> fetchCurrentUser({
    required String token,
    required String email,
  }) async {
    if (mockAuth) {
      return _loadMockProfile(email);
    }
    if (baseUrl.isEmpty) {
      throw ProfileException(
        'Falta la URL base. Configúrala en assets/config/app_config.json o con --dart-define.',
      );
    }
    final response = await _get(path: '/users/me', token: token);
    return _mapProfile(responseBody: response, email: email);
  }

  Future<UserProfile> completeProfile({
    required String token,
    required String email,
    required List<UserInterest> interests,
    required String bio,
  }) async {
    if (mockAuth) {
      final profile = UserProfile(
        email: email,
        profileCompleted: true,
        interests: interests,
        bio: bio,
      );
      await _saveMockProfile(profile);
      return profile;
    }
    if (baseUrl.isEmpty) {
      throw ProfileException(
        'Falta la URL base. Configúrala en assets/config/app_config.json o con --dart-define.',
      );
    }
    final response = await _put(
      path: '/users/me/profile',
      token: token,
      body: {
        'bio': bio,
        'interests': interests.map((i) => i.toJson()).toList(),
        'profileCompleted': true,
      },
    );
    final mapped = _mapProfile(responseBody: response, email: email);
    return mapped.profileCompleted
        ? mapped
        : mapped.copyWith(profileCompleted: true);
  }

  Future<Map<String, dynamic>> _get({
    required String path,
    required String token,
  }) async {
    final uri = _buildUri(path);
    http.Response response;
    try {
      response = await _client.get(
        uri,
        headers: {
          ..._headers,
          'Authorization': 'Bearer $token',
        },
      );
    } catch (e) {
      throw ProfileException('Error de red: $e');
    }
    return _parseResponse(response);
  }

  Future<Map<String, dynamic>> _put({
    required String path,
    required String token,
    required Map<String, dynamic> body,
  }) async {
    final uri = _buildUri(path);
    http.Response response;
    try {
      response = await _client.put(
        uri,
        headers: {
          ..._headers,
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(body),
      );
    } catch (e) {
      throw ProfileException('Error de red: $e');
    }
    return _parseResponse(response);
  }

  Future<Map<String, dynamic>> _parseResponse(http.Response response) async {
    final decoded = _decodeBody(response.body);

    if (response.statusCode == 401) {
      await UnauthorizedHandler.handleUnauthorized();
      throw ProfileException(UnauthorizedHandler.sessionExpiredMessage);
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final message = _extractMessage(decoded) ??
          'La solicitud falló (${response.statusCode}).';
      throw ProfileException(message);
    }
    return decoded;
  }

  Map<String, dynamic> _decodeBody(String body) {
    if (body.isEmpty) return <String, dynamic>{};
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map<String, dynamic>) return decoded;
      return <String, dynamic>{'data': decoded};
    } catch (_) {
      return <String, dynamic>{};
    }
  }

  String? _extractMessage(Map<String, dynamic> body) {
    final candidates = [
      body['message'],
      body['error'],
      body['detail'],
    ];
    for (final candidate in candidates) {
      if (candidate is String && candidate.trim().isNotEmpty) {
        return candidate.trim();
      }
    }
    final errors = body['errors'];
    if (errors is Map<String, dynamic> && errors.isNotEmpty) {
      final first = errors.values.first;
      if (first is List && first.isNotEmpty) {
        final value = first.first;
        if (value is String && value.trim().isNotEmpty) return value.trim();
      } else if (first is String && first.trim().isNotEmpty) {
        return first.trim();
      }
    }
    return null;
  }

  Uri _buildUri(String path) {
    final base = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    return Uri.parse('$base/$cleanPath');
  }

  UserProfile _mapProfile({
    required Map<String, dynamic> responseBody,
    required String email,
  }) {
    final profileJson = _extractProfile(responseBody);
    final profile = UserProfile.fromJson(profileJson);
    final resolvedEmail = profile.email.isNotEmpty
        ? profile.email
        : (_extractEmail(responseBody) ?? email);
    return profile.copyWith(email: resolvedEmail);
  }

  Map<String, dynamic> _extractProfile(Map<String, dynamic> body) {
    final profile = body['profile'];
    if (profile is Map<String, dynamic>) return profile;

    final user = body['user'];
    if (user is Map<String, dynamic>) {
      final userProfile = user['profile'];
      if (userProfile is Map<String, dynamic>) return userProfile;
      return user;
    }

    return body;
  }

  String? _extractEmail(Map<String, dynamic> body) {
    if (body['email'] is String) return body['email'] as String;
    final user = body['user'];
    if (user is Map<String, dynamic> && user['email'] is String) {
      return user['email'] as String;
    }
    final profile = body['profile'];
    if (profile is Map<String, dynamic> && profile['email'] is String) {
      return profile['email'] as String;
    }
    return null;
  }

  Future<UserProfile> _loadMockProfile(String email) async {
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_mockProfileKey);
    if (stored != null) {
      try {
        final decoded = jsonDecode(stored) as Map<String, dynamic>;
        final profile = UserProfile.fromJson(decoded);
        if (profile.email.isEmpty) {
          return profile.copyWith(email: email);
        }
        return profile;
      } catch (_) {
        // ignore and fall through
      }
    }
    return UserProfile(
      email: email,
      profileCompleted: false,
      interests: const [],
      bio: '',
    );
  }

  Future<void> _saveMockProfile(UserProfile profile) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_mockProfileKey, jsonEncode(profile.toJson()));
  }
}
