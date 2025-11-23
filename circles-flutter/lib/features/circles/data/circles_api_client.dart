import 'dart:convert';

import 'package:circles/core/auth/unauthorized_handler.dart';
import 'package:http/http.dart' as http;

import '../../auth/domain/auth_session.dart';
import '../domain/circle.dart';

class CirclesApiClient {
  CirclesApiClient({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  bool get _hasBaseUrl => baseUrl.isNotEmpty;

  Future<List<Circle>> list({required AuthSession session}) async {
    _assertConfigured();

    final response = await _get(
      path: '/circles/me',
      session: session,
    );

    final circlesJson = response['circles'];
    if (circlesJson is List) {
      return circlesJson
          .whereType<Map<String, dynamic>>()
          .map(Circle.fromApiJson)
          .toList();
    }
    return const <Circle>[];
  }

  Future<Circle> create({
    required AuthSession session,
    required Circle draft,
  }) async {
    _assertConfigured();

    final response = await _post(
      path: '/circles',
      session: session,
      body: draft.toApiCreatePayload(),
    );
    final body = response['circle'];
    if (body is Map<String, dynamic>) {
      return Circle.fromApiJson(body);
    }
    throw CircleApiException('Respuesta inesperada al crear círculo.');
  }

  Future<Circle> update({
    required AuthSession session,
    required String id,
    required Circle draft,
  }) async {
    _assertConfigured();

    final response = await _patch(
      path: '/circles/$id',
      session: session,
      body: draft.toApiUpdatePayload(),
    );
    final body = response['circle'];
    if (body is Map<String, dynamic>) {
      return Circle.fromApiJson(body);
    }
    throw CircleApiException('Respuesta inesperada al actualizar círculo.');
  }

  Future<void> delete({
    required AuthSession session,
    required String id,
  }) async {
    _assertConfigured();
    await _delete(path: '/circles/$id', session: session);
  }

  Future<Map<String, dynamic>> _get({
    required String path,
    required AuthSession session,
  }) async {
    final uri = _buildUri(path);
    final response = await _client.get(uri, headers: _headers(session));
    return _processResponse(response);
  }

  Future<Map<String, dynamic>> _post({
    required String path,
    required AuthSession session,
    required Map<String, dynamic> body,
  }) async {
    final uri = _buildUri(path);
    final response = await _client.post(
      uri,
      headers: _headers(session),
      body: jsonEncode(body),
    );
    return _processResponse(response);
  }

  Future<Map<String, dynamic>> _patch({
    required String path,
    required AuthSession session,
    required Map<String, dynamic> body,
  }) async {
    final uri = _buildUri(path);
    final response = await _client.patch(
      uri,
      headers: _headers(session),
      body: jsonEncode(body),
    );
    return _processResponse(response);
  }

  Future<void> _delete({
    required String path,
    required AuthSession session,
  }) async {
    final uri = _buildUri(path);
    final response = await _client.delete(uri, headers: _headers(session));
    await _processResponse(response, expectEmpty: true);
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

  Future<Map<String, dynamic>> _processResponse(
    http.Response response, {
    bool expectEmpty = false,
  }) async {
    final decoded = _decodeBody(response.body);

    if (response.statusCode == 401) {
      await UnauthorizedHandler.handleUnauthorized();
      throw CircleApiException(UnauthorizedHandler.sessionExpiredMessage);
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (expectEmpty) return <String, dynamic>{};
      return decoded;
    }

    final message = _extractMessage(decoded) ??
        'Error ${response.statusCode} en el servidor de círculos.';
    throw CircleApiException(message);
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
      throw CircleApiException(
        'Falta la URL base. Configúrala en assets/config/app_config.json o con --dart-define.',
      );
    }
  }
}

class CircleApiException implements Exception {
  CircleApiException(this.message);
  final String message;

  @override
  String toString() => message;
}
