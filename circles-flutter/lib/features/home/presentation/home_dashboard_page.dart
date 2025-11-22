import 'package:flutter/material.dart';

import '../../../core/widgets/primary_button.dart';
import '../../../core/widgets/page_container.dart';
import '../../app/app_state.dart';

class HomeDashboardPage extends StatelessWidget {
  const HomeDashboardPage({
    super.key,
    required this.onNavigateToCircles,
    required this.onNavigateToMatches,
    required this.state,
    required this.onOpenProfile,
  });

  final VoidCallback onNavigateToCircles;
  final VoidCallback onNavigateToMatches;
  final AppState state;
  final VoidCallback onOpenProfile;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inicio'),
        actions: [
          IconButton(
            onPressed: onOpenProfile,
            tooltip: 'Perfil',
            icon: const Icon(Icons.person_outline),
          ),
        ],
      ),
      body: PageContainer(
        child: ListView(
          children: [
            _StatsGrid(
              circles: state.circles.length,
              matchesForMe: state.matchesForMe.length,
              matchesIAmIn: state.matchesIAmIn.length,
              onCircles: onNavigateToCircles,
              onMatches: onNavigateToMatches,
            ),
            const SizedBox(height: 24),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Siguiente paso',
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Crea tus círculos para encontrar coincidencias cercanas.',
                      style: theme.textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 12),
                    PrimaryButton(
                      label: 'Crear un círculo',
                      icon: Icons.hub,
                      onPressed: onNavigateToCircles,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  const _StatsGrid({
    required this.circles,
    required this.matchesForMe,
    required this.matchesIAmIn,
    required this.onCircles,
    required this.onMatches,
  });

  final int circles;
  final int matchesForMe;
  final int matchesIAmIn;
  final VoidCallback onCircles;
  final VoidCallback onMatches;

  @override
  Widget build(BuildContext context) {
    final cards = [
      _StatCard(
        title: 'Círculos activos',
        value: circles.toString(),
        icon: Icons.hub,
        onTap: onCircles,
      ),
      _StatCard(
        title: 'Matches recibidos',
        value: matchesForMe.toString(),
        icon: Icons.people_alt,
        onTap: onMatches,
      ),
      _StatCard(
        title: 'Matches enviados',
        value: matchesIAmIn.toString(),
        icon: Icons.outbond,
        onTap: onMatches,
      ),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth > 1100
            ? 3
            : constraints.maxWidth > 640
                ? 2
                : 1;
        final aspectRatio = columns == 1
            ? 2.8
            : columns == 2
                ? 2.1
                : 1.6;
        return GridView.count(
          crossAxisCount: columns,
          shrinkWrap: true,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: aspectRatio,
          children: cards,
        );
      },
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    this.onTap,
  });

  final String title;
  final String value;
  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final card = Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor:
                  theme.colorScheme.primary.withValues(alpha: 0.1),
              foregroundColor: theme.colorScheme.primary,
              child: Icon(icon),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.labelLarge,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
    return onTap != null
        ? InkWell(onTap: onTap, borderRadius: BorderRadius.circular(16), child: card)
        : card;
  }
}
