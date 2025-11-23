import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../auth/domain/auth_session.dart';
import '../chats/domain/chat_message.dart';
import '../chats/domain/chat_thread.dart';
import '../circles/domain/circle.dart';
import '../circles/data/circles_api_client.dart';
import '../matches/domain/match_candidate.dart';

class AppState extends ChangeNotifier {
  AppState({
    required AuthSession session,
    required CirclesApiClient circlesApiClient,
  })  : _session = session,
        _circlesApiClient = circlesApiClient;

  final AuthSession _session;
  final CirclesApiClient _circlesApiClient;

  final List<Circle> _circles = [];
  final List<MatchCandidate> _matchesForMe = [];
  final List<MatchCandidate> _matchesIAmIn = [];
  final List<ChatThread> _chats = [];
  bool _loading = false;
  String? _error;

  static const _circlesKey = 'circles_cache_v1';

  List<Circle> get circles => List.unmodifiable(_circles);
  List<MatchCandidate> get matchesForMe => List.unmodifiable(_matchesForMe);
  List<MatchCandidate> get matchesIAmIn => List.unmodifiable(_matchesIAmIn);
  List<ChatThread> get chats => List.unmodifiable(_chats);
  bool get loading => _loading;
  String? get error => _error;

  // Session-scoped UI flags (not persisted)
  bool _hasShownZeroCirclesModal = false;
  bool get hasShownZeroCirclesModal => _hasShownZeroCirclesModal;
  void markZeroCirclesModalShown() {
    _hasShownZeroCirclesModal = true;
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
      if (_circlesApiClient.mockApi || _circlesApiClient.baseUrl.isEmpty) {
        await _loadCirclesFromCacheOrSeed();
      } else {
        await _syncCirclesFromBackend();
      }
      _seedMatchesAndChats();
      _loading = false;
    } catch (e) {
      _error = 'No se pudo cargar tus círculos: $e';
      await _loadCirclesFromCacheOrSeed();
      _loading = false;
    }
    notifyListeners();
  }

  Future<void> saveCircle(Circle circle, {required bool isEditing}) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      Circle saved;
      if (_circlesApiClient.mockApi || _circlesApiClient.baseUrl.isEmpty) {
        saved = _ensureLocalCircle(circle, isEditing: isEditing);
      } else if (isEditing) {
        saved = await _circlesApiClient.update(
          session: _session,
          id: circle.id,
          draft: circle,
        );
      } else {
        saved = await _circlesApiClient.create(
          session: _session,
          draft: circle,
        );
      }

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
      if (!(_circlesApiClient.mockApi || _circlesApiClient.baseUrl.isEmpty)) {
        await _circlesApiClient.delete(session: _session, id: id);
      }
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

  void acceptMatch(String matchId) {
    final match =
        _matchesIAmIn.firstWhere((m) => m.id == matchId, orElse: () => MatchCandidate.empty());
    if (match == MatchCandidate.empty()) return;
    _matchesIAmIn.removeWhere((m) => m.id == matchId);
    _chats.add(
      ChatThread(
        id: 'chat-${DateTime.now().microsecondsSinceEpoch}',
        personId: match.personId,
        personName: match.nombre,
        circleObjective: match.circuloObjetivo,
        lastMessage: '¡Hola! Este es el inicio del chat.',
        unreadCount: 0,
        messages: [
          ChatMessage(
            id: 'm-${DateTime.now().microsecondsSinceEpoch}',
            senderId: match.personId,
            text: '¡Hola! Empecemos a planear.',
            sentAt: DateTime.now(),
          ),
        ],
      ),
    );
    notifyListeners();
  }

  void sendMessage(String chatId, String text) {
    final chatIndex = _chats.indexWhere((c) => c.id == chatId);
    if (chatIndex == -1) return;
    final chat = _chats[chatIndex];
    final msg = ChatMessage(
      id: 'm-${DateTime.now().microsecondsSinceEpoch}',
      senderId: _session.email,
      text: text,
      sentAt: DateTime.now(),
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

  Future<void> _persistCircles() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonList = _circles.map((c) => jsonEncode(c.toJson())).toList();
    await prefs.setStringList(_circlesKey, jsonList);
  }

  Future<void> _loadCirclesFromCacheOrSeed() async {
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getStringList(_circlesKey);
    if (stored != null && stored.isNotEmpty) {
      _circles
        ..clear()
        ..addAll(
          stored
              .map((s) => jsonDecode(s) as Map<String, dynamic>)
              .map(Circle.fromJson),
        );
      return;
    }
    final now = DateTime.now();
    _circles.addAll([
      Circle(
        id: 'c1',
        objetivo: 'Formar equipo para hackathon',
        radiusMeters: 10000,
        expiraEn: now.add(const Duration(days: 10)),
        creadoEn: now.subtract(const Duration(days: 1)),
      ),
      Circle(
        id: 'c2',
        objetivo: 'Salir a correr 10k',
        radiusMeters: 5000,
        expiraEn: null,
        creadoEn: now.subtract(const Duration(days: 2)),
      ),
    ]);
    await _persistCircles();
  }

  Future<void> _syncCirclesFromBackend() async {
    final fetched = await _circlesApiClient.list(session: _session);
    _circles
      ..clear()
      ..addAll(fetched);
    await _persistCircles();
  }

  void _upsertCircle(Circle circle) {
    final idx = _circles.indexWhere((c) => c.id == circle.id);
    if (idx == -1) {
      _circles.add(circle);
    } else {
      _circles[idx] = circle;
    }
  }

  Circle _ensureLocalCircle(Circle circle, {required bool isEditing}) {
    if (isEditing) return circle;
    if (circle.id.isNotEmpty) return circle;
    final now = DateTime.now();
    return Circle(
      id: 'circle-${now.microsecondsSinceEpoch}',
      objetivo: circle.objetivo,
      radiusMeters: circle.radiusMeters,
      expiraEn: circle.expiraEn,
      creadoEn: now,
    );
  }

  void _seedMatchesAndChats() {
    final now = DateTime.now();
    _matchesForMe.addAll([
      MatchCandidate(
        id: 'm1',
        personId: 'p1',
        nombre: 'Camila',
        circuloId: 'c1',
        circuloObjetivo: 'Formar equipo para hackathon',
        distanciaKm: 3,
        expiraEn: now.add(const Duration(days: 9)),
      ),
    ]);

    _matchesIAmIn.addAll([
      MatchCandidate(
        id: 'm2',
        personId: 'p2',
        nombre: 'Luis',
        circuloId: 'other1',
        circuloObjetivo: 'Correr 10k el sábado',
        distanciaKm: 4,
        expiraEn: now.add(const Duration(days: 3)),
      ),
    ]);
  }
}
