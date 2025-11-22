import 'package:circles/features/profile/domain/profile_validator.dart';
import 'package:circles/features/profile/domain/user_profile.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('validateProfileData', () {
    test('fails when interests are empty', () {
      final error = validateProfileData(
        interests: const [],
        bio: 'Este es un perfil válido con más de veinte caracteres.',
      );
      expect(error, isNotNull);
      expect(error, contains('interés'));
    });

    test('fails when bio is too short', () {
      final error = validateProfileData(
        interests: const [UserInterest(title: 'Trabajo', description: 'Dev')],
        bio: 'Muy corto',
        minBioLength: 20,
      );
      expect(error, isNotNull);
      expect(error, contains('20'));
    });

    test('passes with at least one interest and long bio', () {
      final error = validateProfileData(
        interests: const [UserInterest(title: 'Trabajo', description: 'Dev')],
        bio: 'Me gusta construir productos y colaborar con equipos.',
        minBioLength: 20,
      );
      expect(error, isNull);
    });
  });
}
