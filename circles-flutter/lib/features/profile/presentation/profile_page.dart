import 'package:flutter/material.dart';

import '../../auth/domain/auth_session.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key, required this.session, required this.onLogout});

  final AuthSession session;
  final Future<void> Function() onLogout;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Perfil'),
        actions: [
          IconButton(
            onPressed: () => _handleLogout(context),
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    theme.colorScheme.secondary.withValues(alpha: 0.14),
                    theme.colorScheme.tertiary.withValues(alpha: 0.12),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 32,
                    backgroundColor: theme.colorScheme.secondary.withValues(
                      alpha: 0.18,
                    ),
                    foregroundColor: theme.colorScheme.secondary,
                    child: const Icon(Icons.person, size: 32),
                  ),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        session.email.split('@').first,
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(session.email, style: theme.textTheme.bodyMedium),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Card(
              color: theme.colorScheme.primaryContainer.withValues(alpha: 0.8),
              child: ListTile(
                leading: Icon(
                  Icons.mail_outline,
                  color: theme.colorScheme.primary,
                ),
                title: const Text('Correo'),
                subtitle: Text(session.email),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              color: theme.colorScheme.tertiaryContainer.withValues(alpha: 0.7),
              child: ListTile(
                leading: Icon(
                  Icons.location_on_outlined,
                  color: theme.colorScheme.tertiary,
                ),
                title: const Text('Ubicación'),
                subtitle: const Text(
                  'Configura tu ubicación cuando haya backend.',
                ),
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: theme.colorScheme.secondary,
              ),
              onPressed: () => _handleLogout(context),
              icon: const Icon(Icons.logout),
              label: const Text('Cerrar sesión'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleLogout(BuildContext context) async {
    await onLogout();
    if (!context.mounted) return;
    Navigator.of(context).popUntil((route) => route.isFirst);
  }
}