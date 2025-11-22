import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;

class AppConfig {
  AppConfig({
    required this.baseUrl,
    required this.mockAuth,
  });

  final String baseUrl;
  final bool mockAuth;

  static const _assetPath = 'assets/config/app_config.json';

  static Future<AppConfig> load() async {
    try {
      final raw = await rootBundle.loadString(_assetPath);
      final data = jsonDecode(raw) as Map<String, dynamic>;
      return AppConfig(
        baseUrl: (data['baseUrl'] ?? '').toString(),
        mockAuth: (data['mockAuth'] as bool?) ?? true,
      );
    } catch (_) {
      // Fall back to safe defaults if config is missing.
      return AppConfig(baseUrl: '', mockAuth: true);
    }
  }
}
