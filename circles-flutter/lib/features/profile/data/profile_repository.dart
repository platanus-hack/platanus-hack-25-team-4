import '../../auth/domain/auth_session.dart';
import '../domain/user_profile.dart';
import 'profile_api_client.dart';

class ProfileRepository {
  ProfileRepository({required this.apiClient});

  final ProfileApiClient apiClient;

  Future<UserProfile> fetchCurrentUser(AuthSession session) {
    return apiClient.fetchCurrentUser(
      token: session.token,
      email: session.email,
    );
  }

  Future<UserProfile> completeProfile({
    required AuthSession session,
    required List<UserInterest> interests,
    required String bio,
  }) {
    return apiClient.completeProfile(
      token: session.token,
      email: session.email,
      interests: interests,
      bio: bio,
    );
  }
}
