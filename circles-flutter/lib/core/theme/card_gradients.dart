import 'package:flutter/material.dart';

/// Shared gradient used across home hero cards and related surfaces.
LinearGradient homeCardGradient(ColorScheme colorScheme) {
  return LinearGradient(
    colors: [
      colorScheme.primary.withValues(alpha: 0.14),
      colorScheme.secondary.withValues(alpha: 0.12),
      colorScheme.tertiary.withValues(alpha: 0.12),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}
