import 'dart:async';

typedef LogoutCallback = Future<void> Function();

/// Lightweight notifier to coordinate app-wide logout when the API
/// responds with HTTP 401.
class UnauthorizedHandler {
  UnauthorizedHandler._();

  static LogoutCallback? _onUnauthorized;
  static bool _handling = false;

  static const sessionExpiredMessage =
      'Tu sesión expiró. Inicia sesión nuevamente.';

  /// Registers the callback to execute when a 401 is received.
  static void register(LogoutCallback? callback) {
    _onUnauthorized = callback;
  }

  /// Clears the registered callback. Useful when disposing the root widget.
  static void clear() {
    _onUnauthorized = null;
  }

  static Future<void> handleUnauthorized() async {
    final callback = _onUnauthorized;
    if (callback == null || _handling) return;

    _handling = true;
    try {
      await callback();
    } finally {
      _handling = false;
    }
  }
}
