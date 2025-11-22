import 'user_profile.dart';

String? validateProfileData({
  required List<UserInterest> interests,
  required String bio,
  int minBioLength = 20,
}) {
  if (interests.isEmpty) {
    return 'Agrega al menos un interés.';
  }
  final trimmedBio = bio.trim();
  if (trimmedBio.length < minBioLength) {
    return 'La descripción debe tener al menos $minBioLength caracteres.';
  }
  return null;
}
