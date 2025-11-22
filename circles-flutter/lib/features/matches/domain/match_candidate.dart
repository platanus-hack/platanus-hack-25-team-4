class MatchCandidate {
  const MatchCandidate({
    required this.id,
    required this.personId,
    required this.nombre,
    required this.circuloId,
    required this.circuloObjetivo,
    this.distanciaKm,
    this.expiraEn,
  });

  final String id;
  final String personId;
  final String nombre;
  final String circuloId;
  final String circuloObjetivo;
  final double? distanciaKm;
  final DateTime? expiraEn;

  static MatchCandidate empty() => const MatchCandidate(
        id: '',
        personId: '',
        nombre: '',
        circuloId: '',
        circuloObjetivo: '',
      );
}
