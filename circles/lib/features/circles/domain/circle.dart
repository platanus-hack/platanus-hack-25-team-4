class Circle {
  Circle({
    required this.id,
    required this.objetivo,
    required this.radioKm,
    this.descripcion,
    this.expiraEn,
    required this.creadoEn,
  });

  final String id;
  final String objetivo;
  final double radioKm;
  final String? descripcion;
  final DateTime? expiraEn;
  final DateTime creadoEn;

  Circle copyWith({
    String? objetivo,
    double? radioKm,
    String? descripcion,
    DateTime? expiraEn,
  }) {
    return Circle(
      id: id,
      objetivo: objetivo ?? this.objetivo,
      radioKm: radioKm ?? this.radioKm,
      descripcion: descripcion ?? this.descripcion,
      expiraEn: expiraEn ?? this.expiraEn,
      creadoEn: creadoEn,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'objetivo': objetivo,
        'radioKm': radioKm,
        'descripcion': descripcion,
        'expiraEn': expiraEn?.toIso8601String(),
        'creadoEn': creadoEn.toIso8601String(),
      };

  factory Circle.fromJson(Map<String, dynamic> json) {
    return Circle(
      id: json['id'] as String,
      objetivo: json['objetivo'] as String,
      radioKm: (json['radioKm'] as num).toDouble(),
      descripcion: json['descripcion'] as String?,
      expiraEn: json['expiraEn'] != null
          ? DateTime.parse(json['expiraEn'] as String)
          : null,
      creadoEn: DateTime.parse(json['creadoEn'] as String),
    );
  }
}
