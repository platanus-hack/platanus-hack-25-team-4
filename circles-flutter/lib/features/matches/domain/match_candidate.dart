enum MatchStatus {
  pendingAccept,
  active,
  declined,
  expired,
}

enum MatchType {
  match,
  softMatch,
}

class MatchCandidate {
  const MatchCandidate({
    required this.id,
    required this.counterpartName,
    required this.counterpartEmail,
    required this.status,
    required this.type,
    required this.createdAt,
    required this.updatedAt,
    required this.initiatedByMe,
    this.explanation,
    this.primaryCircleId,
    this.secondaryCircleId,
    this.primaryUserId,
    this.secondaryUserId,
  });

  final String id;
  final String counterpartName;
  final String counterpartEmail;
  final MatchStatus status;
  final MatchType type;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool initiatedByMe;
  final String? explanation;
  final String? primaryCircleId;
  final String? secondaryCircleId;
  final String? primaryUserId;
  final String? secondaryUserId;

  bool get isPending => status == MatchStatus.pendingAccept;
  bool get isActive => status == MatchStatus.active;

  MatchCandidate copyWith({
    String? id,
    String? counterpartName,
    String? counterpartEmail,
    MatchStatus? status,
    MatchType? type,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool? initiatedByMe,
    String? explanation,
    String? primaryCircleId,
    String? secondaryCircleId,
    String? primaryUserId,
    String? secondaryUserId,
  }) {
    return MatchCandidate(
      id: id ?? this.id,
      counterpartName: counterpartName ?? this.counterpartName,
      counterpartEmail: counterpartEmail ?? this.counterpartEmail,
      status: status ?? this.status,
      type: type ?? this.type,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      initiatedByMe: initiatedByMe ?? this.initiatedByMe,
      explanation: explanation ?? this.explanation,
      primaryCircleId: primaryCircleId ?? this.primaryCircleId,
      secondaryCircleId: secondaryCircleId ?? this.secondaryCircleId,
      primaryUserId: primaryUserId ?? this.primaryUserId,
      secondaryUserId: secondaryUserId ?? this.secondaryUserId,
    );
  }

  static MatchCandidate empty() => MatchCandidate(
        id: '',
        counterpartName: '',
        counterpartEmail: '',
        status: MatchStatus.pendingAccept,
        type: MatchType.match,
        createdAt: DateTime.fromMillisecondsSinceEpoch(0),
        updatedAt: DateTime.fromMillisecondsSinceEpoch(0),
        initiatedByMe: false,
      );

  factory MatchCandidate.fromApiJson({
    required Map<String, dynamic> json,
    required String currentUserEmail,
  }) {
    final primaryUser = _asMap(json['primaryUser']);
    final secondaryUser = _asMap(json['secondaryUser']);
    final primaryEmail = _asString(primaryUser['email']);
    final secondaryEmail = _asString(secondaryUser['email']);
    final normalizedCurrent = currentUserEmail.trim().toLowerCase();
    final isCurrentPrimary = normalizedCurrent.isNotEmpty &&
        primaryEmail.toLowerCase() == normalizedCurrent;
    final isCurrentSecondary = normalizedCurrent.isNotEmpty &&
        secondaryEmail.toLowerCase() == normalizedCurrent;
    final initiatedByMe = isCurrentPrimary;

    final counterpart = isCurrentPrimary
        ? secondaryUser
        : isCurrentSecondary
            ? primaryUser
            : (primaryUser.isNotEmpty ? primaryUser : secondaryUser);

    final counterpartName =
        _nameFrom(counterpart) ?? _nameFrom(primaryUser) ?? _nameFrom(secondaryUser) ?? 'Persona cerca';
    final counterpartEmail = _asString(counterpart['email']);

    final createdAtRaw = _asString(json['createdAt']);
    final updatedAtRaw = _asString(json['updatedAt']);

    return MatchCandidate(
      id: _asString(json['id']),
      counterpartName: counterpartName,
      counterpartEmail: counterpartEmail,
      status: _statusFrom(_asString(json['status'])),
      type: _typeFrom(_asString(json['type'])),
      explanation: _asString(json['explanationSummary']).isEmpty
          ? null
          : _asString(json['explanationSummary']),
      createdAt: DateTime.tryParse(createdAtRaw) ??
          DateTime.fromMillisecondsSinceEpoch(0),
      updatedAt: DateTime.tryParse(updatedAtRaw) ??
          DateTime.tryParse(createdAtRaw) ??
          DateTime.fromMillisecondsSinceEpoch(0),
      initiatedByMe: initiatedByMe,
      primaryCircleId: _asString(json['primaryCircleId']),
      secondaryCircleId: _asString(json['secondaryCircleId']),
      primaryUserId: _asString(json['primaryUserId']),
      secondaryUserId: _asString(json['secondaryUserId']),
    );
  }
}

MatchStatus _statusFrom(String raw) {
  switch (raw) {
    case 'pending_accept':
      return MatchStatus.pendingAccept;
    case 'active':
      return MatchStatus.active;
    case 'declined':
      return MatchStatus.declined;
    case 'expired':
      return MatchStatus.expired;
    default:
      return MatchStatus.pendingAccept;
  }
}

MatchType _typeFrom(String raw) {
  switch (raw) {
    case 'soft_match':
      return MatchType.softMatch;
    case 'match':
    default:
      return MatchType.match;
  }
}

String _asString(dynamic value) => value?.toString() ?? '';

Map<String, dynamic> _asMap(dynamic value) =>
    value is Map<String, dynamic> ? value : <String, dynamic>{};

String? _nameFrom(Map<String, dynamic> user) {
  final first = _asString(user['firstName']);
  final last = _asString(user['lastName']);
  final email = _asString(user['email']);
  final full = [first, last].where((p) => p.isNotEmpty).join(' ').trim();
  if (full.isNotEmpty) return full;
  if (email.isNotEmpty) return email;
  return null;
}
