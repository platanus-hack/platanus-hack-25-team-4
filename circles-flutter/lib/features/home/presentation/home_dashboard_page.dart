import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../../../core/widgets/app_logo.dart';
import '../../../core/widgets/primary_button.dart';
import '../../../core/widgets/page_container.dart';
import '../../app/app_state.dart';

class HomeDashboardPage extends StatefulWidget {
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
  State<HomeDashboardPage> createState() => _HomeDashboardPageState();
}

class _HomeDashboardPageState extends State<HomeDashboardPage> {
  bool _isModalOpen = false;

  @override
  void initState() {
    super.initState();
    widget.state.refreshCircles();
    widget.state.refreshMatches();
    widget.state.addListener(_onAppStateChanged);
    // Run once after first layout to avoid triggering setState during build.
    SchedulerBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _maybeShowCreateCircleModal();
    });
  }

  @override
  void dispose() {
    widget.state.removeListener(_onAppStateChanged);
    super.dispose();
  }

  void _onAppStateChanged() {
    // Defer the modal check to the next frame so state notifications don't
    // mutate widgets mid-build.
    SchedulerBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _maybeShowCreateCircleModal();
    });
  }

  void _maybeShowCreateCircleModal() {
    if (_isModalOpen ||
        widget.state.loading ||
        !widget.state.hasLoadedUiFlags ||
        widget.state.hasActiveCircles ||
        widget.state.hasShownZeroCirclesModal) {
      return;
    }
    // Mark as shown and persist so it won't appear again on page changes or relaunches
    unawaited(widget.state.markZeroCirclesModalShown());
    SchedulerBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _showCreateCircleModal();
    });
  }

  void _showCreateCircleModal() {
    _isModalOpen = true;
    final theme = Theme.of(context);
    showDialog<void>(
      context: context,
      barrierDismissible: true,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                theme.colorScheme.primary.withValues(alpha: 0.16),
                theme.colorScheme.secondary.withValues(alpha: 0.16),
                theme.colorScheme.tertiary.withValues(alpha: 0.14),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.secondaryContainer.withValues(
                          alpha: 0.9,
                        ),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.auto_awesome, size: 26),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      'Activa tu primer círculo',
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  'Cuenta quién eres y qué buscas para encontrar gente cerca más rápido.',
                  style: theme.textTheme.bodyMedium,
                ),
                const SizedBox(height: 14),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _ColorChip(
                      icon: Icons.lightbulb_outline,
                      label: 'Idea clara',
                      color: theme.colorScheme.primary,
                    ),
                    _ColorChip(
                      icon: Icons.radar_outlined,
                      label: 'Gente cerca',
                      color: theme.colorScheme.secondary,
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: PrimaryButton(
                        label: 'Crear mi primer círculo',
                        icon: Icons.hub,
                        backgroundColor: theme.colorScheme.secondary,
                        onPressed: () {
                          Navigator.of(context).pop();
                          widget.onNavigateToCircles();
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Después'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    ).whenComplete(() {
      _isModalOpen = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final state = widget.state;
    return Scaffold(
      appBar: AppBar(
        title: const AppLogo(text: 'Circles - Inicio'),
        actions: [
          IconButton(
            onPressed: widget.onOpenProfile,
            tooltip: 'Perfil',
            icon: const Icon(Icons.person_outline),
          ),
        ],
      ),
      body: PageContainer(
        child: ListView(
          children: [
            if (state.loading) ...[
              const LinearProgressIndicator(),
              const SizedBox(height: 12),
            ],
            _HeroCard(
              onCircles: widget.onNavigateToCircles,
              onMatches: widget.onNavigateToMatches,
              circles: state.circles.length,
              matches: state.matches.length,
            ),
            const SizedBox(height: 16),
            _StatsGrid(
              circles: state.circles.length,
              pendingMatches: state.pendingMatches.length,
              activeMatches: state.activeMatches.length,
              onCircles: widget.onNavigateToCircles,
              onMatches: widget.onNavigateToMatches,
            ),
            const SizedBox(height: 24),
            Card(
              color: theme.colorScheme.tertiaryContainer.withValues(alpha: 0.6),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Siguiente paso',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
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
                      backgroundColor: theme.colorScheme.secondary,
                      onPressed: widget.onNavigateToCircles,
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

class _ColorChip extends StatelessWidget {
  const _ColorChip({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  const _StatsGrid({
    required this.circles,
    required this.pendingMatches,
    required this.activeMatches,
    required this.onCircles,
    required this.onMatches,
  });

  final int circles;
  final int pendingMatches;
  final int activeMatches;
  final VoidCallback onCircles;
  final VoidCallback onMatches;

  @override
  Widget build(BuildContext context) {
    final cards = [
      _StatCard(
        title: 'Círculos activos',
        value: circles.toString(),
        icon: Icons.hub,
        color: Theme.of(context).colorScheme.primary,
        accent: Theme.of(context).colorScheme.secondary,
        onTap: onCircles,
      ),
      _StatCard(
        title: 'Matches pendientes',
        value: pendingMatches.toString(),
        icon: Icons.hourglass_bottom_outlined,
        color: Theme.of(context).colorScheme.secondary,
        accent: Theme.of(context).colorScheme.tertiary,
        onTap: onMatches,
      ),
      _StatCard(
        title: 'Matches activos',
        value: activeMatches.toString(),
        icon: Icons.handshake,
        color: Theme.of(context).colorScheme.tertiary,
        accent: Theme.of(context).colorScheme.primary,
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
    required this.color,
    required this.accent,
    this.onTap,
  });

  final String title;
  final String value;
  final IconData icon;
  final Color color;
  final Color accent;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isLightColor =
        ThemeData.estimateBrightnessForColor(color) == Brightness.light;
    final gradientStart = color.withValues(alpha: isLightColor ? 0.28 : 0.2);
    final gradientEnd = accent.withValues(alpha: isLightColor ? 0.18 : 0.12);
    final outline = color.withValues(alpha: isLightColor ? 0.32 : 0.22);
    final titleColor = Color.alphaBlend(
      color.withValues(alpha: isLightColor ? 0.6 : 0.45),
      theme.colorScheme.onSurface,
    );
    final avatarBg = color.withValues(alpha: isLightColor ? 0.30 : 0.22);
    final avatarFg = Color.alphaBlend(
      color.withValues(alpha: isLightColor ? 0.7 : 0.5),
      theme.colorScheme.onSurface,
    );
    final card = Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            gradientStart,
            gradientEnd,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(color: outline),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.15),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 26,
              backgroundColor: avatarBg,
              foregroundColor: avatarFg,
              child: Icon(icon),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: titleColor,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onSurface,
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
        ? InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(16),
            child: card,
          )
        : card;
  }
}

class _HeroCard extends StatelessWidget {
  const _HeroCard({
    required this.onCircles,
    required this.onMatches,
    required this.circles,
    required this.matches,
  });

  final VoidCallback onCircles;
  final VoidCallback onMatches;
  final int circles;
  final int matches;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            theme.colorScheme.primary.withValues(alpha: 0.14),
            theme.colorScheme.secondary.withValues(alpha: 0.12),
            theme.colorScheme.tertiary.withValues(alpha: 0.12),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: theme.colorScheme.primary.withValues(alpha: 0.10),
            blurRadius: 10,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: theme.colorScheme.secondaryContainer.withValues(
                    alpha: 0.8,
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.auto_awesome, size: 18),
                    SizedBox(width: 6),
                    Text('Radar activo'),
                  ],
                ),
              ),
              const Spacer(),
              IconButton(
                onPressed: onMatches,
                icon: const Icon(Icons.radar),
                tooltip: 'Ver matches',
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Descubre gente cerca',
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Mantén tus círculos activos para recibir mejores coincidencias.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              Chip(
                avatar: const Icon(Icons.hub_outlined, size: 18),
                label: Text('$circles círculos'),
              ),
              Chip(
                avatar: const Icon(Icons.people_outline, size: 18),
                label: Text('$matches matches'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: PrimaryButton(
                  label: 'Ver mis círculos',
                  icon: Icons.hub,
                  backgroundColor: theme.colorScheme.secondary,
                  onPressed: onCircles,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onMatches,
                  icon: const Icon(Icons.people_outline),
                  label: const Text('Ver matches'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
