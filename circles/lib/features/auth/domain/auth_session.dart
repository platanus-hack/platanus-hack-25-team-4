class AuthSession {
  AuthSession({
    required this.email,
    required this.token,
  });

  final String email;
  final String token;
}

class AuthException implements Exception {
  AuthException(this.message);
  final String message;

  @override
  String toString() => 'AuthException: $message';
}
