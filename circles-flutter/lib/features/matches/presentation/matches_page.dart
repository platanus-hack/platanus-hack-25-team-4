import 'package:flutter/material.dart';

import '../../app/app_state.dart';
import '../../../core/widgets/page_container.dart';
import '../../../core/theme/app_colors.dart';
import '../domain/match_candidate.dart';

class MatchesPage extends StatefulWidget {
  const MatchesPage({
    super.key,
    required this.state,
    required this.onOpenProfile,
  });

  final AppState state;
  final VoidCallback onOpenProfile;

  @override
  State<MatchesPage> createState() => _MatchesPageState();
}

class _MatchesPageState extends State<MatchesPage> {
  final TextEditingController _searchController = TextEditingController();
  String _sort = 'distancia';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final forMe = _filtered(widget.state.matchesForMe);
    final iAmIn = _filtered(widget.state.matchesIAmIn);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Matches'),
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
            _Filters(
              controller: _searchController,
              sort: _sort,
              onSortChanged: (value) => setState(() => _sort = value),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Chip(
                  avatar: const Icon(Icons.inbox_outlined, size: 18),
                  label: Text('Recibidos: ${forMe.length}'),
                ),
                Chip(
                  avatar: const Icon(Icons.outbox_outlined, size: 18),
                  label: Text('Enviados: ${iAmIn.length}'),
                ),
                Chip(
                  avatar: const Icon(Icons.location_pin, size: 18),
                  label: const Text('Buscando cerca de ti'),
                  backgroundColor: theme.colorScheme.secondaryContainer
                      .withValues(alpha: 0.7),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              'Personas que matchean mis círculos',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            forMe.isEmpty
                ? _EmptyList(
                    icon: Icons.people_alt_outlined,
                    message: 'Aún no hay matches en tus círculos.',
                  )
                : _MatchList(matches: forMe),
            const SizedBox(height: 24),
            Text(
              'Personas a las que yo matcheo',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            iAmIn.isEmpty
                ? _EmptyList(
                    icon: Icons.person_search_outlined,
                    message:
                        'Cuando matchees un círculo de alguien podrás aceptar la interacción.',
                  )
                : _MatchList(
                    matches: iAmIn,
                    allowAccept: true,
                    onAccept: widget.state.acceptMatch,
                  ),
          ],
        ),
      ),
    );
  }

  List<MatchCandidate> _filtered(List<MatchCandidate> input) {
    final query = _searchController.text.trim().toLowerCase();
    final list = input.where((m) {
      if (query.isEmpty) return true;
      return m.nombre.toLowerCase().contains(query) ||
          m.circuloObjetivo.toLowerCase().contains(query);
    }).toList();
    list.sort((a, b) {
      switch (_sort) {
        case 'expira':
          final aDate = a.expiraEn ?? DateTime(9999);
          final bDate = b.expiraEn ?? DateTime(9999);
          return aDate.compareTo(bDate);
        case 'nombre':
          return a.nombre.toLowerCase().compareTo(b.nombre.toLowerCase());
        case 'distancia':
        default:
          final aDist = a.distanciaKm ?? double.maxFinite;
          final bDist = b.distanciaKm ?? double.maxFinite;
          return aDist.compareTo(bDist);
      }
    });
    return list;
  }
}

class _EmptyList extends StatelessWidget {
  const _EmptyList({required this.icon, required this.message});

  final IconData icon;
  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.tertiaryContainer.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: theme.colorScheme.outline.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Icon(icon, color: theme.colorScheme.secondary),
          const SizedBox(width: 12),
          Expanded(child: Text(message, style: theme.textTheme.bodyMedium)),
        ],
      ),
    );
  }
}

class _MatchList extends StatelessWidget {
  const _MatchList({
    required this.matches,
    this.allowAccept = false,
    this.onAccept,
  });

  final List<MatchCandidate> matches;
  final bool allowAccept;
  final void Function(String matchId)? onAccept;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final palette = [
      theme.colorScheme.primary,
      theme.colorScheme.secondary,
      theme.colorScheme.tertiary,
      AppColors.accent2,
    ];
    return Column(
      children: matches.asMap().entries.map((entry) {
        final index = entry.key;
        final m = entry.value;
        final accent = palette[index % palette.length];
        return Card(
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: accent.withValues(alpha: 0.18),
              foregroundColor: accent,
              child: const Icon(Icons.person),
            ),
            title: Text(
              m.nombre,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 2),
                Text(
                  m.circuloObjetivo,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: accent,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    _InfoChip(
                      icon: Icons.route,
                      label: m.distanciaKm != null
                          ? '${m.distanciaKm!.toStringAsFixed(1)} km'
                          : 'Distancia no disponible',
                      color: accent,
                    ),
                    if (m.expiraEn != null)
                      _InfoChip(
                        icon: Icons.timer_outlined,
                        label: 'Expira ${_formatDate(m.expiraEn!)}',
                        color: theme.colorScheme.secondary,
                      ),
                  ],
                ),
              ],
            ),
            trailing: allowAccept
                ? FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: theme.colorScheme.secondary,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: onAccept == null ? null : () => onAccept!(m.id),
                    child: const Text('Aceptar'),
                  )
                : null,
          ),
        );
      }).toList(),
    );
  }

  String _formatDate(DateTime date) {
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    final y = date.year.toString();
    return '$d/$m/$y';
  }
}

class _Filters extends StatelessWidget {
  const _Filters({
    required this.controller,
    required this.sort,
    required this.onSortChanged,
    required this.onChanged,
  });

  final TextEditingController controller;
  final String sort;
  final ValueChanged<String> onSortChanged;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            decoration: const InputDecoration(
              hintText: 'Buscar por nombre u objetivo',
              prefixIcon: Icon(Icons.search),
            ),
            onChanged: onChanged,
          ),
        ),
        const SizedBox(width: 12),
        DropdownButton<String>(
          value: sort,
          items: const [
            DropdownMenuItem(value: 'distancia', child: Text('Distancia')),
            DropdownMenuItem(value: 'expira', child: Text('Expira')),
            DropdownMenuItem(value: 'nombre', child: Text('Nombre')),
          ],
          onChanged: (value) {
            if (value != null) onSortChanged(value);
          },
        ),
      ],
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isLightColor =
        ThemeData.estimateBrightnessForColor(color) == Brightness.light;
    final background = color.withOpacity(isLightColor ? 0.22 : 0.16);
    final borderColor = color.withOpacity(isLightColor ? 0.5 : 0.35);
    final foreground = Color.alphaBlend(
      color.withOpacity(isLightColor ? 0.65 : 0.45),
      theme.colorScheme.onSurface,
    );
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: borderColor),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: foreground),
          const SizedBox(width: 6),
          Text(
            label,
            style: theme.textTheme.labelMedium?.copyWith(
              color: foreground,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
