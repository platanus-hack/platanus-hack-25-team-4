import 'package:circles/core/storage/credentials_storage.dart';

import '../domain/auth_session.dart';
import 'auth_api_client.dart';

class AuthRepository {
  AuthRepository({
    required this.apiClient,
    required this.storage,
  });

  final AuthApiClient apiClient;
  final CredentialsStorage storage;

  Future<AuthSession> login(String email, String password) async {
    final session =
        await apiClient.login(email: email.trim(), password: password);
    await storage.saveSession(session);
    return session;
  }

  Future<AuthSession> signUp({
    required String name,
    required String email,
    required String password,
  }) async {
    final session = await apiClient.signUp(
      name: name.trim(),
      email: email.trim(),
      password: password,
    );
    await storage.saveSession(session);
    return session;
  }

  Future<AuthSession?> loadSavedSession() => storage.readSession();

  Future<void> logout() => storage.clear();
}
