import 'dart:convert';

import 'package:http/http.dart' as http;

import '../domain/auth_session.dart';

class AuthApiClient {
  AuthApiClient({
    required this.baseUrl,
    http.Client? client,
    this.mockAuth = true,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;
  final bool mockAuth;
  static const _headers = {'Content-Type': 'application/json'};

  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    if (mockAuth) {
      // Simulated login for local development when no backend is available.
      await Future<void>.delayed(const Duration(milliseconds: 350));
      return AuthSession(
        email: email,
        token: 'mock-token-${DateTime.now().millisecondsSinceEpoch}',
      );
    }

    final response = await _post(
      path: '/auth/login',
      body: {'email': email, 'password': password},
    );

    return _mapSession(responseBody: response, email: email);
  }

  Future<AuthSession> signUp({
    required String name,
    required String email,
    required String password,
  }) async {
    if (mockAuth) {
      await Future<void>.delayed(const Duration(milliseconds: 350));
      return AuthSession(
        email: email,
        token: 'mock-signup-token-${DateTime.now().millisecondsSinceEpoch}',
      );
    }

    final trimmedName = name.trim();
    final response = await _post(
      path: '/auth/signup',
      body: {
        'firstName': trimmedName,
        'email': email,
        'password': password,
      },
    );

    return _mapSession(responseBody: response, email: email);
  }

  Future<Map<String, dynamic>> _post({
    required String path,
    required Map<String, dynamic> body,
  }) async {
    if (baseUrl.isEmpty) {
      throw AuthException(
        'Falta la URL base. Configúrala en assets/config/app_config.json o con --dart-define.',
      );
    }

    final uri = _buildUri(path);

    http.Response response;
    try {
      response = await _client.post(
        uri,
        headers: _headers,
        body: jsonEncode(body),
      );
    } catch (e) {
      throw AuthException('Error de red: $e');
    }

    final decoded = _decodeBody(response.body);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final message = _extractMessage(decoded) ??
          'La solicitud falló (${response.statusCode}).';
      throw AuthException(message);
    }

    return decoded;
  }

  AuthSession _mapSession({
    required Map<String, dynamic> responseBody,
    required String email,
  }) {
    final token = responseBody['token'] ?? responseBody['access_token'];
    if (token == null) {
      throw AuthException('La respuesta no incluye token.');
    }
    final user = responseBody['user'];
    final responseEmail = user is Map<String, dynamic> ? user['email'] : null;
    final resolvedEmail =
        responseEmail is String && responseEmail.isNotEmpty ? responseEmail : email;
    return AuthSession(email: resolvedEmail, token: token.toString());
  }

  Uri _buildUri(String path) {
    final base = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    return Uri.parse('$base/$cleanPath');
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
    final messageCandidates = [
      body['message'],
      body['error'],
      body['detail'],
    ];

    for (final candidate in messageCandidates) {
      if (candidate is String && candidate.trim().isNotEmpty) {
        return candidate.trim();
      }
    }

    // Handle validation errors like { errors: { email: ["taken"] } }
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
}
