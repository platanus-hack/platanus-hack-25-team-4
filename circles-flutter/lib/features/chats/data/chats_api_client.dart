import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../auth/domain/auth_session.dart';

class ChatsApiClient {
  ChatsApiClient({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  bool get _hasBaseUrl => baseUrl.isNotEmpty;

  Future<Map<String, dynamic>> listChats({required AuthSession session}) async {
    _assertConfigured();
    final uri = _buildUri('/chats');
    final response = await _client.get(uri, headers: _headers(session));
    return _processResponse(response);
  }

  Future<Map<String, dynamic>> listMessages({
    required AuthSession session,
    required String chatId,
    int limit = 50,
    int offset = 0,
  }) async {
    _assertConfigured();
    final uri = _buildUri(
      '/chats/$chatId/messages',
      queryParameters: {
        'limit': '$limit',
        'offset': '$offset',
      },
    );
    final response = await _client.get(uri, headers: _headers(session));
    return _processResponse(response);
  }

  Future<Map<String, dynamic>> sendMessage({
    required AuthSession session,
    required String chatId,
    required String content,
    required String receiverId,
  }) async {
    _assertConfigured();
    final uri = _buildUri('/chats/$chatId/messages');
    final response = await _client.post(
      uri,
      headers: _headers(session),
      body: jsonEncode({
        'content': content,
        'receiverId': receiverId,
      }),
    );
    return _processResponse(response);
  }

  Future<Map<String, dynamic>> createChat({
    required AuthSession session,
    required String primaryUserId,
    required String secondaryUserId,
    String? matchId,
  }) async {
    _assertConfigured();
    final uri = _buildUri('/chats');
    final response = await _client.post(
      uri,
      headers: _headers(session),
      body: jsonEncode({
        'primaryUserId': primaryUserId,
        'secondaryUserId': secondaryUserId,
        'matchId': matchId,
      }),
    );
    return _processResponse(response);
  }

  Map<String, dynamic> _processResponse(http.Response response) {
    final decoded = _decodeBody(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }
    final message = _extractMessage(decoded) ??
        'Error ${response.statusCode} al cargar chats.';
    throw ChatsApiException(message);
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

  Uri _buildUri(String path, {Map<String, String>? queryParameters}) {
    final trimmedBase =
        baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    final uri = Uri.parse('$trimmedBase/$cleanPath');
    if (queryParameters == null || queryParameters.isEmpty) return uri;
    return uri.replace(queryParameters: queryParameters);
  }

  void _assertConfigured() {
    if (!_hasBaseUrl) {
      throw ChatsApiException(
        'Falta la URL base. Configúrala en assets/config/app_config.json o con --dart-define.',
      );
    }
  }
}

class ChatsApiException implements Exception {
  ChatsApiException(this.message);
  final String message;

  @override
  String toString() => message;
}
