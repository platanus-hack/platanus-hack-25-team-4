import 'package:flutter/material.dart';

import '../../../core/widgets/app_logo.dart';
import '../../auth/domain/auth_session.dart';
import '../data/profile_repository.dart';
import '../domain/user_profile.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({
    super.key,
    required this.session,
    required this.repository,
    required this.onLogout,
  });

  final AuthSession session;
  final ProfileRepository repository;
  final Future<void> Function() onLogout;

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  late Future<UserProfile> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.repository.fetchCurrentUser(widget.session);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const AppLogo(text: 'Circles - Perfil'),
        actions: [
          IconButton(
            onPressed: () => _handleLogout(context),
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: FutureBuilder<UserProfile>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline, size: 40),
                    const SizedBox(height: 8),
                    Text('No pudimos cargar tu perfil. ${snapshot.error}'),
                    const SizedBox(height: 12),
                    FilledButton(
                      onPressed: () {
                        setState(() {
                          _future = widget.repository.fetchCurrentUser(widget.session);
                        });
                      },
                      child: const Text('Reintentar'),
                    ),
                  ],
                ),
              );
            }
            final profile = snapshot.data!;
            return LayoutBuilder(
              builder: (context, constraints) {
                return Align(
                  alignment: Alignment.topCenter,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 760),
                    child: ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        _HeaderCard(email: profile.email, theme: theme),
                        const SizedBox(height: 24),
                        _InfoCard(
                          icon: Icons.mail_outline,
                          title: 'Correo',
                          subtitle: profile.email,
                          color: theme.colorScheme.primary,
                          bg: theme.colorScheme.primaryContainer.withValues(alpha: 0.8),
                        ),
                        const SizedBox(height: 12),
                        _InfoCard(
                          icon: Icons.badge_outlined,
                          title: 'Bio',
                          subtitle: profile.bio.isNotEmpty
                              ? profile.bio
                              : 'Aún no agregas una bio.',
                          color: theme.colorScheme.secondary,
                          bg: theme.colorScheme.secondaryContainer.withValues(alpha: 0.7),
                        ),
                        const SizedBox(height: 12),
                        _InterestsSection(profile: profile),
                        const SizedBox(height: 12),
                        _LocationCard(profile: profile, theme: theme),
                        if (profile.availability != null &&
                            profile.availability!.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          _InfoCard(
                            icon: Icons.schedule_outlined,
                            title: 'Disponibilidad',
                            subtitle: profile.availability!,
                            color: theme.colorScheme.tertiary,
                            bg: theme.colorScheme.tertiaryContainer.withValues(alpha: 0.7),
                          ),
                        ],
                        if (profile.boundaries.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          _InfoCard(
                            icon: Icons.shield_moon_outlined,
                            title: 'Límites',
                            subtitle: profile.boundaries.join(' • '),
                            color: theme.colorScheme.outline,
                            bg: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.8),
                          ),
                        ],
                        const SizedBox(height: 32),
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: FilledButton.icon(
                            style: FilledButton.styleFrom(
                              backgroundColor: theme.colorScheme.secondary,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                            ),
                            onPressed: () => _handleLogout(context),
                            icon: const Icon(Icons.logout),
                            label: const Text('Cerrar sesión'),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }

  Future<void> _handleLogout(BuildContext context) async {
    await widget.onLogout();
    if (!context.mounted) return;
    Navigator.of(context).popUntil((route) => route.isFirst);
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.email, required this.theme});

  final String email;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final username = email.split('@').first;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            theme.colorScheme.secondaryContainer.withValues(alpha: 0.25),
            theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 32,
            backgroundColor: theme.colorScheme.secondary.withValues(alpha: 0.18),
            foregroundColor: theme.colorScheme.secondary,
            child: const Icon(Icons.person, size: 32),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  username,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(email, style: theme.textTheme.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.bg,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final Color bg;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      color: bg,
      child: ListTile(
        leading: Icon(icon, color: color),
        title: Text(title),
        subtitle: Text(
          subtitle,
          style: TextStyle(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
          ),
        ),
      ),
    );
  }
}

class _InterestsSection extends StatelessWidget {
  const _InterestsSection({required this.profile});

  final UserProfile profile;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (profile.interests.isEmpty) {
      return _InfoCard(
        icon: Icons.favorite_border,
        title: 'Intereses',
        subtitle: 'Aún no agregas intereses.',
        color: theme.colorScheme.primary,
        bg: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
      );
    }
    return Card(
      color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.favorite, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Intereses',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: profile.interests
                  .map(
                    (i) => Chip(
                      label: Text(i.title),
                      avatar: Icon(Icons.auto_awesome,
                          size: 16, color: theme.colorScheme.primary),
                      backgroundColor:
                          theme.colorScheme.primaryContainer.withValues(alpha: 0.25),
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class _LocationCard extends StatelessWidget {
  const _LocationCard({required this.profile, required this.theme});

  final UserProfile profile;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
      child: ListTile(
        leading: Icon(
          Icons.location_on_outlined,
          color: theme.colorScheme.tertiary,
        ),
        title: const Text('Ubicación'),
        subtitle: const Text(
          'Se envía en segundo plano cuando autorizas ubicación siempre. '
          'Actívala en ajustes si aún no aparece.',
        ),
      ),
    );
  }
}
