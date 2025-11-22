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
        'radiusMeters': radiusMeters,
        'expiraEn': expiraEn?.toIso8601String(),
        'creadoEn': creadoEn.toIso8601String(),
      };

  factory Circle.fromJson(Map<String, dynamic> json) {
    return Circle(
      id: json['id'] as String,
      objetivo: json['objetivo'] as String,
      radiusMeters: (json['radiusMeters'] as num).toDouble(),
      expiraEn: json['expiraEn'] != null
          ? DateTime.parse(json['expiraEn'] as String)
          : null,
      creadoEn: DateTime.parse(json['creadoEn'] as String),
    );
  }
}
