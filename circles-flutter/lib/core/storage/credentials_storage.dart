import 'package:shared_preferences/shared_preferences.dart';

import '../../features/auth/domain/auth_session.dart';

class CredentialsStorage {
  static const tokenKey = 'auth_token';
  static const emailKey = 'auth_email';

  Future<void> saveSession(AuthSession session) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(tokenKey, session.token);
    await prefs.setString(emailKey, session.email);
  }

  Future<AuthSession?> readSession() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(tokenKey);
    final email = prefs.getString(emailKey);
    if (token == null || email == null) return null;
    return AuthSession(email: email, token: token);
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(tokenKey);
    await prefs.remove(emailKey);
  }
}
