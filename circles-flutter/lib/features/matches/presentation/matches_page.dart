import 'package:flutter/material.dart';

import '../../app/app_state.dart';
import '../../../core/widgets/app_logo.dart';
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
  String _sort = 'recientes';
  String? _acceptingId;
  String? _decliningId;

  @override
  void initState() {
    super.initState();
    widget.state.refreshMatches();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final filtered = _applyFilters(widget.state.matches);
    final pending =
        filtered.where((m) => m.status == MatchStatus.pendingAccept).toList();
    final active =
        filtered.where((m) => m.status == MatchStatus.active).toList();
    final history = filtered
        .where((m) =>
            m.status == MatchStatus.declined || m.status == MatchStatus.expired)
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const AppLogo(text: 'Circles - Matches'),
        actions: [
          IconButton(
            onPressed: widget.onOpenProfile,
            tooltip: 'Perfil',
            icon: const Icon(Icons.person_outline),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => widget.state.refreshMatches(force: true),
        child: PageContainer(
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              if (widget.state.error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.errorContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error_outline, color: theme.colorScheme.onErrorContainer),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          widget.state.error!,
                          style: TextStyle(color: theme.colorScheme.onErrorContainer),
                        ),
                      ),
                      IconButton(
                        onPressed: () => widget.state.refreshMatches(force: true),
                        icon: Icon(Icons.refresh, color: theme.colorScheme.onErrorContainer),
                        tooltip: 'Reintentar',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
              ],
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
                    avatar: const Icon(Icons.people, size: 18),
                    label: Text('Total: ${filtered.length}'),
                  ),
                  Chip(
                    avatar: const Icon(Icons.hourglass_bottom, size: 18),
                    label: Text('Pendientes: ${pending.length}'),
                    backgroundColor:
                        theme.colorScheme.secondaryContainer.withValues(alpha: 0.7),
                  ),
                  Chip(
                    avatar: const Icon(Icons.handshake, size: 18),
                    label: Text('Activos: ${active.length}'),
                    backgroundColor:
                        theme.colorScheme.tertiaryContainer.withValues(alpha: 0.7),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const _SectionHeader(
                label: 'Pendientes de respuesta',
                icon: Icons.schedule,
              ),
              pending.isEmpty
                  ? const _EmptyList(
                      icon: Icons.people_outline,
                      message: 'No hay matches pendientes por ahora.',
                    )
                : _MatchList(
                    matches: pending,
                    allowAccept: true,
                    onAccept: _handleAccept,
                    onDecline: _handleDecline,
                    busyMatchId: _acceptingId,
                    decliningMatchId: _decliningId,
                  ),
              const SizedBox(height: 24),
              const _SectionHeader(
                label: 'Activos',
                icon: Icons.handshake,
              ),
              active.isEmpty
                  ? const _EmptyList(
                      icon: Icons.handshake_outlined,
                      message:
                          'Acepta un match para comenzar a conectar con alguien.',
                    )
                  : _MatchList(matches: active),
              if (history.isNotEmpty) ...[
                const SizedBox(height: 24),
                const _SectionHeader(
                  label: 'Historial',
                  icon: Icons.history,
                ),
                _MatchList(matches: history),
              ],
            ],
          ),
        ),
      ),
    );
  }

  List<MatchCandidate> _applyFilters(List<MatchCandidate> input) {
    final query = _searchController.text.trim().toLowerCase();
    final list = input.where((m) {
      if (query.isEmpty) return true;
      return m.counterpartName.toLowerCase().contains(query) ||
          m.counterpartEmail.toLowerCase().contains(query);
    }).toList();
    list.sort((a, b) {
      switch (_sort) {
        case 'nombre':
          return a.counterpartName
              .toLowerCase()
              .compareTo(b.counterpartName.toLowerCase());
        case 'estado':
          return _statusOrder(a.status).compareTo(_statusOrder(b.status));
        case 'recientes':
        default:
          return b.updatedAt.compareTo(a.updatedAt);
      }
    });
    return list;
  }

  int _statusOrder(MatchStatus status) {
    switch (status) {
      case MatchStatus.pendingAccept:
        return 0;
      case MatchStatus.active:
        return 1;
      case MatchStatus.declined:
        return 2;
      case MatchStatus.expired:
        return 3;
    }
  }

  Future<void> _handleAccept(String matchId) async {
    if (_acceptingId != null || _decliningId != null) return;
    setState(() => _acceptingId = matchId);
    try {
      await widget.state.acceptMatch(matchId);
      if (!mounted) return;
      _showSnack('Match aceptado, conversa cuando quieras.');
    } catch (e) {
      if (!mounted) return;
      _showSnack('No pudimos aceptar el match: $e');
    } finally {
      if (mounted) setState(() => _acceptingId = null);
    }
  }

  Future<void> _handleDecline(String matchId) async {
    if (_acceptingId != null || _decliningId != null) return;
    setState(() => _decliningId = matchId);
    try {
      await widget.state.declineMatch(matchId);
      if (!mounted) return;
      _showSnack('Match rechazado.');
    } catch (e) {
      if (!mounted) return;
      _showSnack('No pudimos rechazar el match: $e');
    } finally {
      if (mounted) setState(() => _decliningId = null);
    }
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.label, required this.icon});

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Icon(icon, color: theme.colorScheme.primary),
        const SizedBox(width: 8),
        Text(
          label,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
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
        border: Border.all(color: theme.colorScheme.outline.withValues(alpha: 0.2)),
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
    this.onDecline,
    this.busyMatchId,
    this.decliningMatchId,
  });

  final List<MatchCandidate> matches;
  final bool allowAccept;
  final Future<void> Function(String matchId)? onAccept;
  final Future<void> Function(String matchId)? onDecline;
  final String? busyMatchId;
  final String? decliningMatchId;

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
        final statusColor = _statusColor(theme, m.status);
        final isBusy = busyMatchId == m.id;
        final isDeclining = decliningMatchId == m.id;
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(
                    backgroundColor: accent.withValues(alpha: 0.18),
                    foregroundColor: accent,
                    child: const Icon(Icons.person),
                  ),
                  title: Text(
                    m.counterpartName,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  subtitle: Text(
                    m.counterpartEmail.isNotEmpty
                        ? m.counterpartEmail
                        : 'Usuario sin correo visible',
                  ),
                  trailing: allowAccept
                      ? Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            TextButton(
                              onPressed: (onDecline == null || isDeclining || isBusy)
                                  ? null
                                  : () => onDecline!(m.id),
                              child: isDeclining
                                  ? const SizedBox(
                                      height: 16,
                                      width: 16,
                                      child: CircularProgressIndicator(strokeWidth: 2),
                                    )
                                  : const Text('Rechazar'),
                            ),
                            const SizedBox(width: 6),
                            FilledButton(
                              style: FilledButton.styleFrom(
                                backgroundColor: theme.colorScheme.secondary,
                                foregroundColor: theme.colorScheme.onSecondary,
                              ),
                              onPressed: (onAccept == null || isBusy || isDeclining)
                                  ? null
                                  : () => onAccept!(m.id),
                              child: isBusy
                                  ? const SizedBox(
                                      height: 16,
                                      width: 16,
                                      child: CircularProgressIndicator(strokeWidth: 2),
                                    )
                                  : const Text('Aceptar'),
                            ),
                          ],
                        )
                      : null,
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    _InfoChip(
                      icon: Icons.bolt,
                      label: _statusLabel(m.status),
                      color: statusColor,
                    ),
                    _InfoChip(
                      icon: Icons.category_outlined,
                      label: _typeLabel(m.type),
                      color: accent,
                    ),
                    _InfoChip(
                      icon: Icons.update,
                      label: _relativeTime(m.updatedAt),
                      color: theme.colorScheme.outline,
                    ),
                    _InfoChip(
                      icon: Icons.swap_horiz,
                      label: m.initiatedByMe
                          ? 'Lo iniciaste tú'
                          : 'Te encontraron',
                      color: AppColors.accent2,
                    ),
                  ],
                ),
                if (m.explanation != null && m.explanation!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    m.explanation!,
                    style: theme.textTheme.bodyMedium,
                  ),
                ],
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Color _statusColor(ThemeData theme, MatchStatus status) {
    switch (status) {
      case MatchStatus.pendingAccept:
        return theme.colorScheme.secondary;
      case MatchStatus.active:
        return theme.colorScheme.primary;
      case MatchStatus.declined:
        return theme.colorScheme.error;
      case MatchStatus.expired:
        return theme.colorScheme.outline;
    }
  }

  String _statusLabel(MatchStatus status) {
    switch (status) {
      case MatchStatus.pendingAccept:
        return 'Pendiente';
      case MatchStatus.active:
        return 'Activo';
      case MatchStatus.declined:
        return 'Rechazado';
      case MatchStatus.expired:
        return 'Expirado';
    }
  }

  String _typeLabel(MatchType type) {
    switch (type) {
      case MatchType.softMatch:
        return 'Soft match';
      case MatchType.match:
        return 'Match directo';
    }
  }

  String _relativeTime(DateTime date) {
    final diff = DateTime.now().difference(date);
    if (diff.inMinutes < 1) return 'ahora';
    if (diff.inHours < 1) return 'hace ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'hace ${diff.inHours} h';
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    return '$d/$m';
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
              hintText: 'Buscar por persona o correo',
              prefixIcon: Icon(Icons.search),
            ),
            onChanged: onChanged,
          ),
        ),
        const SizedBox(width: 12),
        DropdownButton<String>(
          value: sort,
          items: const [
            DropdownMenuItem(value: 'recientes', child: Text('Recientes')),
            DropdownMenuItem(value: 'nombre', child: Text('Nombre')),
            DropdownMenuItem(value: 'estado', child: Text('Estado')),
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
    return Chip(
      avatar: Icon(icon, size: 16, color: color),
      label: Text(label),
      backgroundColor: color.withValues(alpha: 0.12),
      labelStyle: TextStyle(color: color),
      side: BorderSide(color: color.withValues(alpha: 0.4)),
    );
  }
}
