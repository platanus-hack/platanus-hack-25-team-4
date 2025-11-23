class Circle {
  Circle({
    required this.id,
    required this.objetivo,
    required this.radiusMeters,
    this.expiraEn,
    required this.creadoEn,
  });

  final String id;
  final String objetivo;
  final double radiusMeters; // Stored in meters
  final DateTime? expiraEn;
  final DateTime creadoEn;

  /// Convenience getter to convert meters to kilometers
  double get radiusKm => radiusMeters / 1000;

  Circle copyWith({
    String? objetivo,
    double? radiusMeters,
    DateTime? expiraEn,
  }) {
    return Circle(
      id: id,
      objetivo: objetivo ?? this.objetivo,
      radiusMeters: radiusMeters ?? this.radiusMeters,
      expiraEn: expiraEn ?? this.expiraEn,
      creadoEn: creadoEn,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'objetivo': objetivo,
        'objective': objetivo, // keep English key for API-aligned caches
        'radiusMeters': radiusMeters,
        'expiraEn': expiraEn?.toIso8601String(),
        'expiresAt': expiraEn?.toIso8601String(),
        'creadoEn': creadoEn.toIso8601String(),
        'createdAt': creadoEn.toIso8601String(),
      };

  /// Parses persisted JSON (cache) or API responses using English keys.
  factory Circle.fromJson(Map<String, dynamic> json) {
    final objetivoValue =
        (json['objective'] ?? json['objetivo'])?.toString() ?? '';
    final radiusValue = json['radiusMeters'];
    final parsedRadius =
        radiusValue is num ? radiusValue.toDouble() : 0.0;
    return Circle(
      id: json['id'] as String,
      objetivo: objetivoValue,
      radiusMeters: parsedRadius,
      expiraEn: _parseDate(json['expiresAt'] ?? json['expiraEn']),
      creadoEn:
          _parseDate(json['createdAt'] ?? json['creadoEn']) ?? DateTime.now(),
    );
  }

  factory Circle.fromApiJson(Map<String, dynamic> json) {
    final radiusValue = json['radiusMeters'];
    final parsedRadius =
        radiusValue is num ? radiusValue.toDouble() : 0.0;
    return Circle(
      id: (json['id'] ?? json['circleId']).toString(),
      objetivo: (json['objective'] ?? json['objective'] ?? '').toString(),
      radiusMeters: parsedRadius,
      expiraEn: _parseDate(json['expiresAt']),
      creadoEn: _parseDate(json['createdAt']) ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toApiCreatePayload() => {
        'objective': objetivo,
        'radiusMeters': radiusMeters,
        if (expiraEn != null) 'expiresAt': expiraEn!.toIso8601String(),
      };

  Map<String, dynamic> toApiUpdatePayload() => {
        if (objetivo.isNotEmpty) 'objective': objetivo,
        'radiusMeters': radiusMeters,
        'expiresAt': expiraEn?.toIso8601String(),
      };

  static DateTime? _parseDate(Object? value) {
    if (value == null) return null;
    if (value is DateTime) return value;
    if (value is String && value.isNotEmpty) {
      return DateTime.tryParse(value);
    }
    return null;
  }
}
