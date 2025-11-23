import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../auth/domain/auth_session.dart';
import '../domain/match_candidate.dart';

class MatchesApiClient {
  MatchesApiClient({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  bool get _hasBaseUrl => baseUrl.isNotEmpty;

  Future<List<MatchCandidate>> list({
    required AuthSession session,
    int limit = 50,
    int offset = 0,
  }) async {
    _assertConfigured();

    final response = await _get(
      path: '/matches',
      session: session,
      queryParameters: {
        'limit': limit.toString(),
        'offset': offset.toString(),
      },
    );

    final matchesJson = response['matches'];
    if (matchesJson is List) {
      return matchesJson
          .whereType<Map<String, dynamic>>()
          .map(
            (m) => MatchCandidate.fromApiJson(
              json: m,
              currentUserEmail: session.email,
            ),
          )
          .toList();
    }
    return const <MatchCandidate>[];
  }

  Future<Map<String, dynamic>> accept({
    required AuthSession session,
    required String matchId,
  }) async {
    _assertConfigured();
    return _post(path: '/matches/$matchId/accept', session: session);
  }

  Future<Map<String, dynamic>> decline({
    required AuthSession session,
    required String matchId,
  }) async {
    _assertConfigured();
    return _post(path: '/matches/$matchId/decline', session: session);
  }

  Future<Map<String, dynamic>> _get({
    required String path,
    required AuthSession session,
    Map<String, String>? queryParameters,
  }) async {
    final uri = _buildUri(path, queryParameters: queryParameters);
    final response = await _client.get(uri, headers: _headers(session));
    return _processResponse(response);
  }

  Future<Map<String, dynamic>> _post({
    required String path,
    required AuthSession session,
    Map<String, dynamic>? body,
  }) async {
    final uri = _buildUri(path);
    final response = await _client.post(
      uri,
      headers: _headers(session),
      body: body == null ? null : jsonEncode(body),
    );
    return _processResponse(response);
  }

  Map<String, dynamic> _processResponse(
    http.Response response, {
    bool expectEmpty = false,
  }) {
    final decoded = _decodeBody(response.body);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (expectEmpty) return <String, dynamic>{};
      return decoded;
    }

    final message = _extractMessage(decoded) ??
        'Error ${response.statusCode} al cargar matches.';
    throw MatchesApiException(message);
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

  Map<String, String> _headers(AuthSession session) => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${session.token}',
      };

  Uri _buildUri(
    String path, {
    Map<String, String>? queryParameters,
  }) {
    final trimmedBase =
        baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    final uri = Uri.parse('$trimmedBase/$cleanPath');
    if (queryParameters == null || queryParameters.isEmpty) return uri;
    return uri.replace(queryParameters: queryParameters);
  }

  void _assertConfigured() {
    if (!_hasBaseUrl) {
      throw MatchesApiException(
        'Falta la URL base. Configúrala en assets/config/app_config.json o con --dart-define.',
      );
    }
  }
}

class MatchesApiException implements Exception {
  MatchesApiException(this.message);
  final String message;

  @override
  String toString() => message;
}
