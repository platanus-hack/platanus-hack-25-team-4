import 'package:flutter/material.dart';

import '../../app/app_state.dart';
import '../../../core/widgets/page_container.dart';
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
            const SizedBox(height: 16),
            Text(
              'Personas que matchean mis círculos',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
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
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
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
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, color: theme.colorScheme.primary),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: theme.textTheme.bodyMedium,
            ),
          ),
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
    return Column(
      children: matches
          .map(
            (m) => Card(
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor:
                      theme.colorScheme.primary.withValues(alpha: 0.1),
                  foregroundColor: theme.colorScheme.primary,
                  child: const Icon(Icons.person),
                ),
                title: Text(
                  m.nombre,
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w600),
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Objetivo: ${m.circuloObjetivo}',
                      style: theme.textTheme.bodyMedium,
                    ),
                    if (m.distanciaKm != null)
                      Text(
                        'Distancia: ${m.distanciaKm!.toStringAsFixed(1)} km',
                        style: theme.textTheme.bodySmall,
                      ),
                    if (m.expiraEn != null)
                      Text(
                        'Expira: ${_formatDate(m.expiraEn!)}',
                        style: theme.textTheme.bodySmall,
                      ),
                  ],
                ),
                trailing: allowAccept
                    ? FilledButton(
                        onPressed:
                            onAccept == null ? null : () => onAccept!(m.id),
                        child: const Text('Aceptar'),
                      )
                    : null,
              ),
            ),
          )
          .toList(),
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
            DropdownMenuItem(
              value: 'distancia',
              child: Text('Distancia'),
            ),
            DropdownMenuItem(
              value: 'expira',
              child: Text('Expira'),
            ),
            DropdownMenuItem(
              value: 'nombre',
              child: Text('Nombre'),
            ),
          ],
          onChanged: (value) {
            if (value != null) onSortChanged(value);
          },
        ),
      ],
    );
  }
}
