import 'package:flutter/material.dart';

import '../../../core/widgets/primary_button.dart';
import '../../../core/widgets/page_container.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/card_gradients.dart';
import '../../../core/widgets/app_logo.dart';
import '../../app/app_state.dart';
import '../domain/circle.dart';

class CirclesPage extends StatefulWidget {
  const CirclesPage({
    super.key,
    required this.state,
    required this.onOpenProfile,
  });

  final AppState state;
  final VoidCallback onOpenProfile;

  @override
  State<CirclesPage> createState() => _CirclesPageState();
}

class _CirclesPageState extends State<CirclesPage> {
  final TextEditingController _searchController = TextEditingController();
  String _sort = 'creado';

  @override
  void initState() {
    super.initState();
    widget.state.refreshCircles();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final filtered = _filteredCircles();
    final hasItems = filtered.isNotEmpty;
    return Scaffold(
      appBar: AppBar(
        title: const AppLogo(),
        actions: [
          IconButton(
            onPressed: () => _openForm(context),
            tooltip: 'Agregar círculo',
            icon: const Icon(Icons.add),
          ),
          IconButton(
            onPressed: widget.onOpenProfile,
            tooltip: 'Perfil',
            icon: const Icon(Icons.person_outline),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: PageContainer(
          child: Column(
            children: [
              _Filters(
                controller: _searchController,
                sort: _sort,
                onSortChanged: (value) => setState(() => _sort = value),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 12),
              if (widget.state.loading) ...[
                const LinearProgressIndicator(),
                const SizedBox(height: 12),
              ],
              Expanded(
                child: hasItems
                    ? _buildList(context, filtered)
                    : _buildEmpty(theme),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: hasItems
          ? FloatingActionButton.extended(
              onPressed: () => _openForm(context),
              icon: const Icon(Icons.add),
              label: const Text('Crear círculo'),
            )
          : null,
    );
  }

  Widget _buildEmpty(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: theme.colorScheme.secondaryContainer.withValues(
                alpha: 0.6,
              ),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.hub_outlined,
              size: 48,
              color: theme.colorScheme.secondary,
            ),
          ),
          const SizedBox(height: 12),
          Text('Aún no tienes círculos', style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            'Crea un círculo con tu objetivo, fecha límite opcional y radio de búsqueda.',
            style: theme.textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          PrimaryButton(
            label: 'Crear círculo',
            icon: Icons.add,
            backgroundColor: theme.colorScheme.secondary,
            onPressed: () => _openForm(context),
          ),
        ],
      ),
    );
  }

  Widget _buildList(BuildContext context, List<Circle> circles) {
    final theme = Theme.of(context);
    final accentPalette = [
      theme.colorScheme.primary,
      theme.colorScheme.secondary,
      theme.colorScheme.tertiary,
      AppColors.accent2,
    ];
    return ListView.separated(
      itemCount: circles.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final circle = circles[index];
        final accent = accentPalette[index % accentPalette.length];
        return Card(
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: accent.withValues(alpha: 0.18),
              foregroundColor: accent,
              child: const Icon(Icons.hub),
            ),
            title: Text(
              circle.objetivo,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    _InfoPill(
                      icon: Icons.radar,
                      label: 'Radio: ${circle.radiusKm.toStringAsFixed(0)} km',
                      color: accent,
                    ),
                    if (circle.expiraEn != null)
                      _InfoPill(
                        icon: Icons.event_outlined,
                        label: 'Expira: ${_formatDate(circle.expiraEn!)}',
                        color: theme.colorScheme.secondary,
                      ),
                  ],
                ),
              ],
            ),
            trailing: PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'edit') _openForm(context, existing: circle);
                if (value == 'delete') _deleteCircle(circle);
              },
              itemBuilder: (context) => const [
                PopupMenuItem(value: 'edit', child: Text('Editar')),
                PopupMenuItem(value: 'delete', child: Text('Eliminar')),
              ],
            ),
          ),
        );
      },
    );
  }

  void _deleteCircle(Circle circle) async {
    final messenger = ScaffoldMessenger.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        scrollable: true,
        insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
        title: const Text('Eliminar círculo'),
        content: Text('¿Seguro que quieres eliminar "${circle.objetivo}"?'),
        actionsPadding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.state.deleteCircle(circle.id);
      if (!mounted) return;
      messenger.showSnackBar(SnackBar(content: Text('"${circle.objetivo}" eliminado')));
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('Error al eliminar: $e')),
      );
    }
  }

  void _openForm(BuildContext context, {Circle? existing}) async {
    final messenger = ScaffoldMessenger.of(context);
    final result = await showModalBottomSheet<Circle>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      constraints: BoxConstraints(
        // Keep a comfortable width on large screens
        maxWidth: MediaQuery.of(context).size.width > 600.0
            ? 600.0
            : MediaQuery.of(context).size.width,
      ),
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: _CircleForm(existing: existing),
      ),
    );
    if (result == null) return;
    try {
      await widget.state.saveCircle(result, isEditing: existing != null);
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            existing != null ? 'Círculo actualizado' : 'Círculo creado',
          ),
        ),
      );
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('No pudimos guardar: $e')),
      );
    }
  }

  String _formatDate(DateTime date) {
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    final y = date.year.toString();
    return '$d/$m/$y';
  }

  List<Circle> _filteredCircles() {
    final query = _searchController.text.trim().toLowerCase();
    List<Circle> list = widget.state.circles.where((c) {
      if (query.isEmpty) return true;
      return c.objetivo.toLowerCase().contains(query);
    }).toList();

    list.sort((a, b) {
      switch (_sort) {
        case 'expira':
          final aDate = a.expiraEn ?? DateTime(9999);
          final bDate = b.expiraEn ?? DateTime(9999);
          return aDate.compareTo(bDate);
        case 'radio':
          return a.radiusKm.compareTo(b.radiusKm);
        case 'creado':
        default:
          return b.creadoEn.compareTo(a.creadoEn);
      }
    });
    return list;
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
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: homeCardGradient(theme.colorScheme),
        border: Border.all(
          color: theme.colorScheme.primary.withOpacity(0.18),
        ),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Buscar por objetivo',
                prefixIcon: Icon(Icons.search),
              ),
              onChanged: onChanged,
            ),
          ),
          const SizedBox(width: 12),
          DecoratedBox(
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: theme.colorScheme.outlineVariant),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: DropdownButton<String>(
                value: sort,
                underline: const SizedBox.shrink(),
                items: const [
                  DropdownMenuItem(value: 'creado', child: Text('Reciente')),
                  DropdownMenuItem(
                    value: 'expira',
                    child: Text('Expira antes'),
                  ),
                  DropdownMenuItem(value: 'radio', child: Text('Radio menor')),
                ],
                onChanged: (value) {
                  if (value != null) onSortChanged(value);
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CircleForm extends StatefulWidget {
  const _CircleForm({this.existing});

  final Circle? existing;

  @override
  State<_CircleForm> createState() => _CircleFormState();
}

class _CircleFormState extends State<_CircleForm> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _objetivoController;
  double _radioKm = 10;
  DateTime? _expiraEn;

  @override
  void initState() {
    super.initState();
    _objetivoController = TextEditingController(
      text: widget.existing?.objetivo ?? '',
    );
    _radioKm = widget.existing?.radiusKm ?? 10;
    _expiraEn = widget.existing?.expiraEn;
  }

  @override
  void dispose() {
    _objetivoController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isEditing = widget.existing != null;
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    isEditing ? 'Editar círculo' : 'Nuevo círculo',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _objetivoController,
                decoration: const InputDecoration(
                  labelText: 'Objetivo',
                  hintText: 'Ej: Encontrar equipo para hackathon',
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'El objetivo es obligatorio';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              Text('Radio de búsqueda: ${_radioKm.toStringAsFixed(0)} km'),
              Slider(
                value: _radioKm,
                min: 1,
                max: 100,
                divisions: 99,
                label: '${_radioKm.toStringAsFixed(0)} km',
                activeColor: theme.colorScheme.secondary,
                thumbColor: theme.colorScheme.secondary,
                onChanged: (value) => setState(() => _radioKm = value),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      _expiraEn == null
                          ? 'Sin fecha límite'
                          : 'Expira: ${_formatDateTime(_expiraEn!)}',
                    ),
                  ),
                  TextButton.icon(
                    onPressed: _pickDateTime,
                    icon: const Icon(Icons.event),
                    label: const Text('Elegir fecha y hora'),
                  ),
                  if (_expiraEn != null)
                    IconButton(
                      onPressed: () => setState(() => _expiraEn = null),
                      tooltip: 'Quitar fecha',
                      icon: const Icon(Icons.clear),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              PrimaryButton(
                label: isEditing ? 'Guardar cambios' : 'Crear círculo',
                icon: Icons.check,
                backgroundColor: theme.colorScheme.secondary,
                onPressed: _submit,
              ),
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _pickDateTime() async {
    final now = DateTime.now();
    final initial = _expiraEn ?? now.add(const Duration(days: 7));
    final selectedDate = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
      helpText: 'Selecciona fecha de expiración (opcional)',
      cancelText: 'Cancelar',
      confirmText: 'Aceptar',
    );
    if (selectedDate == null) return;
    if (!mounted) return;

    final selectedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initial),
      helpText: 'Selecciona hora de expiración',
      cancelText: 'Cancelar',
      confirmText: 'Aceptar',
    );
    if (selectedTime == null) return;
    if (!mounted) return;

    final combined = DateTime(
      selectedDate.year,
      selectedDate.month,
      selectedDate.day,
      selectedTime.hour,
      selectedTime.minute,
    );
    setState(() => _expiraEn = combined);
  }

  void _submit() {
    final form = _formKey.currentState;
    if (form == null || !form.validate()) return;
    final now = DateTime.now();
    final circle =
        widget.existing?.copyWith(
          objetivo: _objetivoController.text.trim(),
          radiusMeters: _radioKm * 1000,
          expiraEn: _expiraEn,
        ) ??
        Circle(
          id: 'circle-${now.microsecondsSinceEpoch}',
          objetivo: _objetivoController.text.trim(),
          radiusMeters: _radioKm * 1000,
          expiraEn: _expiraEn,
          creadoEn: now,
        );
    Navigator.pop(context, circle);
  }

  String _formatDateTime(DateTime date) {
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    final y = date.year.toString();
    final hh = date.hour.toString().padLeft(2, '0');
    final mm = date.minute.toString().padLeft(2, '0');
    return '$d/$m/$y $hh:$mm';
  }
}

class _InfoPill extends StatelessWidget {
  const _InfoPill({
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
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.4)),
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
