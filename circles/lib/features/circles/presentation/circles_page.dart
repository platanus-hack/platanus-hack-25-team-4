import 'package:flutter/material.dart';

import '../../../core/widgets/primary_button.dart';
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
        title: const Text('Círculos'),
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
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _Filters(
              controller: _searchController,
              sort: _sort,
              onSortChanged: (value) => setState(() => _sort = value),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: hasItems
                  ? _buildList(context, filtered)
                  : _buildEmpty(theme),
            ),
          ],
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
          Icon(Icons.hub_outlined, size: 64, color: theme.colorScheme.primary),
          const SizedBox(height: 12),
          Text(
            'Aún no tienes círculos',
            style: theme.textTheme.titleMedium,
          ),
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
            onPressed: () => _openForm(context),
          ),
        ],
      ),
    );
  }

  Widget _buildList(BuildContext context, List<Circle> circles) {
    final theme = Theme.of(context);
    return ListView.separated(
      itemCount: circles.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final circle = circles[index];
        return Card(
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor:
                  theme.colorScheme.primary.withValues(alpha: 0.1),
              foregroundColor: theme.colorScheme.primary,
              child: const Icon(Icons.hub),
            ),
            title: Text(
              circle.objetivo,
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (circle.descripcion != null &&
                    circle.descripcion!.trim().isNotEmpty)
                  Text(
                    circle.descripcion!,
                    style: theme.textTheme.bodyMedium,
                  ),
                const SizedBox(height: 4),
                Text(
                  'Radio: ${circle.radioKm.toStringAsFixed(0)} km',
                  style: theme.textTheme.bodySmall,
                ),
                if (circle.expiraEn != null)
                  Text(
                    'Expira: ${_formatDate(circle.expiraEn!)}',
                    style: theme.textTheme.bodySmall,
                  ),
              ],
            ),
            trailing: PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'edit') _openForm(context, existing: circle);
                if (value == 'delete') _deleteCircle(circle);
              },
              itemBuilder: (context) => const [
                PopupMenuItem(
                  value: 'edit',
                  child: Text('Editar'),
                ),
                PopupMenuItem(
                  value: 'delete',
                  child: Text('Eliminar'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _deleteCircle(Circle circle) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Eliminar círculo'),
        content: Text(
          '¿Seguro que quieres eliminar "${circle.objetivo}"?',
        ),
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
    widget.state.deleteCircle(circle.id);
  }

  void _openForm(BuildContext context, {Circle? existing}) async {
    final result = await showModalBottomSheet<Circle>(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: _CircleForm(existing: existing),
      ),
    );
    if (result == null) return;
    widget.state.addOrUpdateCircle(result);
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
      return c.objetivo.toLowerCase().contains(query) ||
          (c.descripcion?.toLowerCase().contains(query) ?? false);
    }).toList();

    list.sort((a, b) {
      switch (_sort) {
        case 'expira':
          final aDate = a.expiraEn ?? DateTime(9999);
          final bDate = b.expiraEn ?? DateTime(9999);
          return aDate.compareTo(bDate);
        case 'radio':
          return a.radioKm.compareTo(b.radioKm);
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
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            decoration: const InputDecoration(
              hintText: 'Buscar por objetivo o descripción',
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
              value: 'creado',
              child: Text('Reciente'),
            ),
            DropdownMenuItem(
              value: 'expira',
              child: Text('Expira antes'),
            ),
            DropdownMenuItem(
              value: 'radio',
              child: Text('Radio menor'),
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

class _CircleForm extends StatefulWidget {
  const _CircleForm({this.existing});

  final Circle? existing;

  @override
  State<_CircleForm> createState() => _CircleFormState();
}

class _CircleFormState extends State<_CircleForm> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _objetivoController;
  late TextEditingController _descripcionController;
  double _radioKm = 10;
  DateTime? _expiraEn;

  @override
  void initState() {
    super.initState();
    _objetivoController =
        TextEditingController(text: widget.existing?.objetivo ?? '');
    _descripcionController =
        TextEditingController(text: widget.existing?.descripcion ?? '');
    _radioKm = widget.existing?.radioKm ?? 10;
    _expiraEn = widget.existing?.expiraEn;
  }

  @override
  void dispose() {
    _objetivoController.dispose();
    _descripcionController.dispose();
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
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  isEditing ? 'Editar círculo' : 'Nuevo círculo',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w600),
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
            TextFormField(
              controller: _descripcionController,
              decoration: const InputDecoration(
                labelText: 'Descripción (opcional)',
              ),
              minLines: 2,
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            Text('Radio de búsqueda: ${_radioKm.toStringAsFixed(0)} km'),
            Slider(
              value: _radioKm,
              min: 1,
              max: 100,
              divisions: 99,
              label: '${_radioKm.toStringAsFixed(0)} km',
              onChanged: (value) => setState(() => _radioKm = value),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Text(
                    _expiraEn == null
                        ? 'Sin fecha límite'
                        : 'Expira: ${_formatDate(_expiraEn!)}',
                  ),
                ),
                TextButton.icon(
                  onPressed: _pickDate,
                  icon: const Icon(Icons.event),
                  label: const Text('Elegir fecha'),
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
              onPressed: _submit,
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final selected = await showDatePicker(
      context: context,
      initialDate: _expiraEn ?? now.add(const Duration(days: 7)),
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
      helpText: 'Selecciona fecha de expiración (opcional)',
      cancelText: 'Cancelar',
      confirmText: 'Aceptar',
    );
    if (selected != null) {
      setState(() => _expiraEn = selected);
    }
  }

  void _submit() {
    final form = _formKey.currentState;
    if (form == null || !form.validate()) return;
    final now = DateTime.now();
    final circle = widget.existing?.copyWith(
          objetivo: _objetivoController.text.trim(),
          descripcion: _descripcionController.text.trim().isEmpty
              ? null
              : _descripcionController.text.trim(),
          radioKm: _radioKm,
          expiraEn: _expiraEn,
        ) ??
        Circle(
          id: 'circle-${now.microsecondsSinceEpoch}',
          objetivo: _objetivoController.text.trim(),
          descripcion: _descripcionController.text.trim().isEmpty
              ? null
              : _descripcionController.text.trim(),
          radioKm: _radioKm,
          expiraEn: _expiraEn,
          creadoEn: now,
        );
    Navigator.pop(context, circle);
  }

  String _formatDate(DateTime date) {
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    final y = date.year.toString();
    return '$d/$m/$y';
  }
}
