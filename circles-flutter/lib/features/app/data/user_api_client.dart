import 'dart:convert';

import 'package:circles/core/auth/unauthorized_handler.dart';
import 'package:http/http.dart' as http;

import '../../auth/domain/auth_session.dart';

class UserApiClient {
  UserApiClient({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  bool get _hasBaseUrl => baseUrl.isNotEmpty;

  Future<String?> getCurrentUserId({required AuthSession session}) async {
    _assertConfigured();
    final uri = _buildUri('/users/me');
    final response = await _client.get(uri, headers: _headers(session));
    final decoded = _decodeBody(response.body);

    if (response.statusCode == 401) {
      await UnauthorizedHandler.handleUnauthorized();
      throw UserApiException(UnauthorizedHandler.sessionExpiredMessage);
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final message = _extractMessage(decoded) ??
          'No se pudo obtener el usuario actual (${response.statusCode}).';
      throw UserApiException(message);
    }
    final id = decoded['id'];
    if (id is! String || id.isEmpty) {
      throw UserApiException('Respuesta inválida: falta el id de usuario.');
    }
    return id;
  }

  Map<String, String> _headers(AuthSession session) => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${session.token}',
      };

  Uri _buildUri(String path) {
    final trimmedBase =
        baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    return Uri.parse('$trimmedBase/$cleanPath');
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
      if (candidate is String && candidate.isNotEmpty) return candidate;
    }
    return null;
  }

  void _assertConfigured() {
    if (!_hasBaseUrl) {
      throw UserApiException(
        'Falta la URL base. Configúrala en assets/config/app_config.json o con --dart-define.',
      );
    }
  }
}

class UserApiException implements Exception {
  UserApiException(this.message);
  final String message;

  @override
  String toString() => message;
}
