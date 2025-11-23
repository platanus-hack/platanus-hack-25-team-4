import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../auth/domain/auth_session.dart';
import '../chats/domain/chat_message.dart';
import '../chats/domain/chat_thread.dart';
import '../chats/data/chats_api_client.dart';
import '../circles/domain/circle.dart';
import '../circles/data/circles_api_client.dart';
import 'data/user_api_client.dart';
import '../matches/data/matches_api_client.dart';
import '../matches/domain/match_candidate.dart';

class AppState extends ChangeNotifier {
  AppState({
    required AuthSession session,
    required CirclesApiClient circlesApiClient,
    required MatchesApiClient matchesApiClient,
    required ChatsApiClient chatsApiClient,
    required UserApiClient userApiClient,
  })  : _session = session,
        _circlesApiClient = circlesApiClient,
        _matchesApiClient = matchesApiClient,
        _chatsApiClient = chatsApiClient,
        _userApiClient = userApiClient;

  final AuthSession _session;
  final CirclesApiClient _circlesApiClient;
  final MatchesApiClient _matchesApiClient;
  final ChatsApiClient _chatsApiClient;
  final UserApiClient _userApiClient;
  String? _userId;

  final List<Circle> _circles = [];
  final List<MatchCandidate> _matches = [];
  final List<ChatThread> _chats = [];
  bool _loading = false;
  String? _error;
  bool _syncedCirclesFromBackend = false;
  bool _syncedMatchesFromBackend = false;
  bool _syncedChatsFromBackend = false;
  bool _hasLoadedUiFlags = false;

  static const _circlesKey = 'circles_cache_v1';
  static const _zeroCirclesModalKey = 'has_seen_zero_circles_modal_v1';

  List<Circle> get circles => List.unmodifiable(_circles);
  List<MatchCandidate> get matches => List.unmodifiable(_matches);
  List<MatchCandidate> get pendingMatches =>
      _matches.where((m) => m.status == MatchStatus.pendingAccept).toList();
  List<MatchCandidate> get activeMatches =>
      _matches.where((m) => m.status == MatchStatus.active).toList();
  List<ChatThread> get chats => List.unmodifiable(_chats);
  bool get loading => _loading;
  String? get error => _error;
  String? get userId => _userId;
  String get currentIdentity => _userId ?? _session.email;

  // UI flags persisted locally
  bool _hasShownZeroCirclesModal = false;
  bool get hasShownZeroCirclesModal => _hasShownZeroCirclesModal;
  bool get hasLoadedUiFlags => _hasLoadedUiFlags;
  Future<void> markZeroCirclesModalShown() async {
    if (_hasShownZeroCirclesModal) return;
    _hasShownZeroCirclesModal = true;
    notifyListeners();
    await _persistZeroCirclesModalFlag();
  }

  // Active circles are those without expiration or with a future expiration
  bool get hasActiveCircles {
    final now = DateTime.now();
    return _circles.any((c) => c.expiraEn == null || (c.expiraEn?.isAfter(now) ?? false));
  }

  Future<void> initialize() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await _loadUiFlags();
      _userId = await _userApiClient.getCurrentUserId(session: _session);
      await _syncCirclesFromBackend();
      await _syncMatchesFromBackend();
      await _syncChatsFromBackend();
      _syncedCirclesFromBackend = true;
      _syncedMatchesFromBackend = true;
      _syncedChatsFromBackend = true;
    } catch (e) {
      _error = 'No se pudo cargar tus datos: $e';
      _circles.clear();
      _matches.clear();
      _chats.clear();
      _syncedCirclesFromBackend = false;
      _syncedMatchesFromBackend = false;
      _syncedChatsFromBackend = false;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> refreshCircles({bool force = false}) async {
    if (_loading) return;

    if (_syncedCirclesFromBackend && !force) return;

    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await _syncCirclesFromBackend();
      _syncedCirclesFromBackend = true;
    } catch (e) {
      _error = 'No se pudo actualizar tus círculos: $e';
      _circles.clear();
      _syncedCirclesFromBackend = false;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> refreshMatches({bool force = false}) async {
    if (_loading) return;
    if (_syncedMatchesFromBackend && !force) return;

    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await _syncMatchesFromBackend();
      _syncedMatchesFromBackend = true;
    } catch (e) {
      _error = 'No se pudo actualizar tus matches: $e';
      _matches.clear();
      _syncedMatchesFromBackend = false;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> refreshChats({bool force = false}) async {
    if (_loading) return;
    if (_syncedChatsFromBackend && !force) return;

    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await _syncChatsFromBackend();
      _syncedChatsFromBackend = true;
    } catch (e) {
      _error = 'No se pudo actualizar tus chats: $e';
      _chats.clear();
      _syncedChatsFromBackend = false;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> saveCircle(Circle circle, {required bool isEditing}) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final saved = isEditing
          ? await _circlesApiClient.update(
              session: _session,
              id: circle.id,
              draft: circle,
            )
          : await _circlesApiClient.create(
              session: _session,
              draft: circle,
            );

      _upsertCircle(saved);
      await _persistCircles();
    } catch (e) {
      _error = 'No pudimos guardar el círculo. ${e.toString()}';
      rethrow;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> deleteCircle(String id) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await _circlesApiClient.delete(session: _session, id: id);
      _circles.removeWhere((c) => c.id == id);
      await _persistCircles();
    } catch (e) {
      _error = 'No pudimos eliminar el círculo. ${e.toString()}';
      rethrow;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> acceptMatch(String matchId) async {
    final index = _matches.indexWhere((m) => m.id == matchId);
    if (index == -1) return;
    try {
      await _matchesApiClient.accept(session: _session, matchId: matchId);
      _matches[index] = _matches[index].copyWith(
        status: MatchStatus.active,
        updatedAt: DateTime.now(),
      );
      await _ensureChatForMatch(_matches[index]);
    } catch (e) {
      _error = 'No pudimos aceptar el match: $e';
      rethrow;
    } finally {
      notifyListeners();
    }
  }

  Future<void> declineMatch(String matchId) async {
    final index = _matches.indexWhere((m) => m.id == matchId);
    if (index == -1) return;
    try {
      await _matchesApiClient.decline(session: _session, matchId: matchId);
      _matches[index] = _matches[index].copyWith(
        status: MatchStatus.declined,
        updatedAt: DateTime.now(),
      );
    } catch (e) {
      _error = 'No pudimos rechazar el match: $e';
      rethrow;
    } finally {
      notifyListeners();
    }
  }

  Future<void> loadMessagesForChat(String chatId) async {
    try {
      final response = await _chatsApiClient.listMessages(
        session: _session,
        chatId: chatId,
        limit: 50,
        offset: 0,
      );
      final data = response['data'];
      if (data is List) {
        final messages = data
            .whereType<Map<String, dynamic>>()
            .map(ChatMessage.fromApi)
            .toList();
        _upsertChatMessages(chatId, messages);
      }
    } catch (e) {
      _error = 'No se pudieron cargar mensajes: $e';
      rethrow;
    } finally {
      notifyListeners();
    }
  }

  Future<void> sendMessage(String chatId, String text) async {
    final chatIndex = _chats.indexWhere((c) => c.id == chatId);
    if (chatIndex == -1) return;
    final receiverId = _chats[chatIndex].personId;
    if (receiverId.isEmpty) {
      _error = 'No encontramos a la persona destinataria.';
      notifyListeners();
      return;
    }
    late final ChatMessage apiMessage;
    try {
      final response = await _chatsApiClient.sendMessage(
        session: _session,
        chatId: chatId,
        content: text,
        receiverId: receiverId,
      );
      apiMessage = ChatMessage.fromApi(response);
    } catch (e) {
      _error = 'No pudimos enviar el mensaje: $e';
      notifyListeners();
      rethrow;
    }
    final chat = _chats[chatIndex];
    final msg = ChatMessage(
      id: apiMessage.id,
      senderId: apiMessage.senderId,
      receiverId: apiMessage.receiverId ?? receiverId,
      text: apiMessage.text,
      sentAt: apiMessage.sentAt,
    );
    final updated = chat.copyWith(
      messages: [...chat.messages, msg],
      lastMessage: text,
      unreadCount: 0,
    );
    _chats[chatIndex] = updated;
    notifyListeners();
  }

  ChatThread? chatById(String id) =>
      _chats.firstWhere((c) => c.id == id, orElse: () => ChatThread.empty());

  Future<void> _loadUiFlags() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _hasShownZeroCirclesModal =
          prefs.getBool(_zeroCirclesModalKey) ?? _hasShownZeroCirclesModal;
    } catch (_) {
      // Best-effort: ignore persistence errors for UI hints.
    } finally {
      _hasLoadedUiFlags = true;
      notifyListeners();
    }
  }

  Future<void> _persistZeroCirclesModalFlag() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_zeroCirclesModalKey, true);
    } catch (_) {
      // Best-effort: ignore persistence errors for UI hints.
    }
  }

  Future<void> _persistCircles() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonList = _circles.map((c) => jsonEncode(c.toJson())).toList();
    await prefs.setStringList(_circlesKey, jsonList);
  }

  Future<void> _syncCirclesFromBackend() async {
    final fetched = await _circlesApiClient.list(session: _session);
    _circles
      ..clear()
      ..addAll(fetched);
    await _persistCircles();
  }

  Future<void> _syncMatchesFromBackend() async {
    final fetched = await _matchesApiClient.list(session: _session);
    _matches
      ..clear()
      ..addAll(fetched);
  }

  Future<void> _syncChatsFromBackend() async {
    final response = await _chatsApiClient.listChats(session: _session);
    final data = response['data'];
    if (data is! List) {
      _chats.clear();
      return;
    }
    _chats
      ..clear()
      ..addAll(
        data.whereType<Map<String, dynamic>>().map((chatJson) {
          final primaryId = (chatJson['primaryUserId'] ?? '').toString();
          final secondaryId = (chatJson['secondaryUserId'] ?? '').toString();
          final currentId = _userId ?? '';
          final isPrimary = currentId.isNotEmpty && primaryId == currentId;
          final isSecondary = currentId.isNotEmpty && secondaryId == currentId;
          final counterpart = isPrimary
              ? _asMap(chatJson['secondaryUser'])
              : isSecondary
                  ? _asMap(chatJson['primaryUser'])
                  : _asMap(chatJson['secondaryUser']);
          final String counterpartId =
              counterpart['id']?.toString().isNotEmpty == true
                  ? counterpart['id'].toString()
                  : (isPrimary ? secondaryId : primaryId);
          final counterpartName = _nameFrom(counterpart) ??
              _nameFrom(_asMap(chatJson['primaryUser'])) ??
              _nameFrom(_asMap(chatJson['secondaryUser'])) ??
              'Persona';
          final latestMessage = chatJson['latestMessage'];
          final lastMessageText = latestMessage is Map<String, dynamic>
              ? (latestMessage['content'] ?? '').toString()
              : null;
          return ChatThread(
            id: (chatJson['id'] ?? '').toString(),
            personId: counterpartId,
            personName: counterpartName,
            circleObjective: null,
            lastMessage: lastMessageText,
            unreadCount: 0,
            messages: const [],
          ).copyWith(
            messages: const [],
            lastMessage: lastMessageText,
          );
        }),
      );
  }

  void _upsertCircle(Circle circle) {
    final idx = _circles.indexWhere((c) => c.id == circle.id);
    if (idx == -1) {
      _circles.add(circle);
    } else {
      _circles[idx] = circle;
    }
  }

  void _upsertChatMessages(String chatId, List<ChatMessage> messages) {
    final idx = _chats.indexWhere((c) => c.id == chatId);
    if (idx == -1) return;
    final sorted = [...messages]..sort((a, b) => a.sentAt.compareTo(b.sentAt));
    final lastText = sorted.isNotEmpty ? sorted.last.text : _chats[idx].lastMessage;
    _chats[idx] = _chats[idx].copyWith(
      messages: sorted,
      lastMessage: lastText,
      unreadCount: 0,
    );
  }

  Future<void> _ensureChatForMatch(MatchCandidate match) async {
    if (_userId == null || _userId!.isEmpty) return;
    final otherUserId = match.primaryUserId == _userId
        ? match.secondaryUserId
        : match.primaryUserId;
    if (otherUserId == null || otherUserId.isEmpty) return;

    // Avoid duplicates
    final existing = _chats.any((c) => c.personId == otherUserId);
    if (existing) return;

    try {
      final chatJson = await _chatsApiClient.createChat(
        session: _session,
        primaryUserId: _userId!,
        secondaryUserId: otherUserId,
        matchId: match.id,
      );
      final counterpartName = match.counterpartName;
      final chat = ChatThread(
        id: (chatJson['id'] ?? '').toString(),
        personId: otherUserId,
        personName: counterpartName,
        circleObjective: null,
        lastMessage: null,
        unreadCount: 0,
        messages: const [],
      );
      _chats.add(chat);
    } catch (_) {
      // Ignore chat creation failures; match accept already succeeded.
    }
  }

  Map<String, dynamic> _asMap(dynamic value) =>
      value is Map<String, dynamic> ? value : <String, dynamic>{};

  String? _nameFrom(Map<String, dynamic> user) {
    final first = (user['firstName'] ?? '').toString();
    final last = (user['lastName'] ?? '').toString();
    final email = (user['email'] ?? '').toString();
    final full = [first, last].where((p) => p.isNotEmpty).join(' ').trim();
    if (full.isNotEmpty) return full;
    if (email.isNotEmpty) return email;
    return null;
  }
}
