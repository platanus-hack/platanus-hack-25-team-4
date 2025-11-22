import 'package:flutter/material.dart';

import '../../auth/domain/auth_session.dart';
import '../../../core/widgets/primary_button.dart';
import '../data/profile_repository.dart';
import '../domain/profile_validator.dart';
import '../domain/user_profile.dart';

class ProfileWizardPage extends StatefulWidget {
  const ProfileWizardPage({
    super.key,
    required this.session,
    required this.repository,
    required this.onCompleted,
    required this.onLogout,
    this.initialBio,
    this.initialInterests = const [],
  });

  final AuthSession session;
  final ProfileRepository repository;
  final ValueChanged<UserProfile> onCompleted;
  final Future<void> Function() onLogout;
  final String? initialBio;
  final List<UserInterest> initialInterests;

  @override
  State<ProfileWizardPage> createState() => _ProfileWizardPageState();
}

class _ProfileWizardPageState extends State<ProfileWizardPage> {
  final _bioController = TextEditingController();
  final _customTitleController = TextEditingController();
  final _customDescController = TextEditingController();
  final Map<String, TextEditingController> _presetControllers = {};
  final Set<String> _selectedPresets = {};
  final List<UserInterest> _customInterests = [];
  bool _customInputExpanded = false;
  bool _submitting = false;
  String? _error;

  static const _presets = <_Preset>[
    _Preset(
      title: 'Trabajo',
      icon: Icons.work_outline,
      placeholder: 'Busco / Ofrezco trabajo, soy dev y busco startups',
    ),
    _Preset(
      title: 'Videojuegos',
      icon: Icons.sports_esports_outlined,
      placeholder: 'Juego Valorant, LoL, etc',
    ),
    _Preset(
      title: 'Deporte',
      icon: Icons.directions_run_outlined,
      placeholder: 'Juego Padel, corro, etc',
    ),
    _Preset(
      title: 'Literatura',
      icon: Icons.menu_book_outlined,
      placeholder: 'Me encantan los libros de ciencia ficción',
    ),
    _Preset(
      title: 'Salir a tomar algo',
      icon: Icons.local_bar_outlined,
      placeholder: 'Me interesa ir a un bar...',
    ),
    _Preset(
      title: 'Buscar pareja',
      icon: Icons.favorite_border,
      placeholder: 'Busco una persona que...',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _bioController.text = widget.initialBio ?? '';
    for (final preset in _presets) {
      _presetControllers[preset.title] = TextEditingController();
    }
    _seedInitialInterests();
  }

  @override
  void dispose() {
    _bioController.dispose();
    _customTitleController.dispose();
    _customDescController.dispose();
    for (final controller in _presetControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  void _seedInitialInterests() {
    for (final interest in widget.initialInterests) {
      final preset = _presets.firstWhere(
        (p) => p.title.toLowerCase() == interest.title.toLowerCase(),
        orElse: () => _Preset.empty,
      );
      if (preset == _Preset.empty) {
        _customInterests.add(interest);
      } else {
        _selectedPresets.add(preset.title);
        final controller = _presetControllers[preset.title];
        controller?.text = interest.description;
      }
    }
    _customInputExpanded = _customInterests.isNotEmpty;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Completa tu perfil'),
        actions: [
          IconButton(
            onPressed: _submitting
                ? null
                : () {
                    widget.onLogout();
                  },
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final isWide = constraints.maxWidth >= 900;
            final cardWidth = constraints.maxWidth > 760
                ? (constraints.maxWidth - 24) / 2
                : constraints.maxWidth;
            final adjustedWidth = cardWidth
                .clamp(260.0, constraints.maxWidth)
                .toDouble();
            final customCardSelected =
                _customInputExpanded ||
                _customInterests.isNotEmpty ||
                _customTitleController.text.isNotEmpty ||
                _customDescController.text.isNotEmpty;

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Align(
                alignment: Alignment.topCenter,
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minHeight: constraints.maxHeight > 32
                        ? constraints.maxHeight - 32
                        : 0,
                    maxWidth: isWide ? 1040 : constraints.maxWidth,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Queremos conocerte',
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Elige intereses y cuéntanos de ti para recomendarte mejores círculos.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: const [
                          _AccentChip(
                            icon: Icons.rocket_launch_outlined,
                            label: 'Destaca lo que te mueve',
                          ),
                          _AccentChip(
                            icon: Icons.radar_outlined,
                            label: 'Mejoramos tus matches',
                          ),
                        ],
                      ),
                      Text(
                        'Intereses',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        alignment: isWide
                            ? WrapAlignment.center
                            : WrapAlignment.start,
                        children: [
                          ..._presets.map(
                            (preset) => SizedBox(
                              width: adjustedWidth,
                              child: _PresetCard(
                                preset: preset,
                                selected: _selectedPresets.contains(
                                  preset.title,
                                ),
                                controller: _presetControllers[preset.title]!,
                                onToggle: () => _togglePreset(preset.title),
                              ),
                            ),
                          ),
                          SizedBox(
                            width: adjustedWidth,
                            child: _CustomInterestInputCard(
                              selected: customCardSelected,
                              titleController: _customTitleController,
                              descController: _customDescController,
                              submitting: _submitting,
                              onToggle: _toggleCustomInterestCard,
                              onAdd: _addCustomInterest,
                            ),
                          ),
                        ],
                      ),
                      if (_customInterests.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: _customInterests
                              .map(
                                (interest) => Padding(
                                  padding: const EdgeInsets.only(bottom: 8),
                                  child: _CustomInterestCard(
                                    interest: interest,
                                    onDelete: _submitting
                                        ? null
                                        : () => _removeCustomInterest(interest),
                                  ),
                                ),
                              )
                              .toList(),
                        ),
                      ],
                      const SizedBox(height: 16),
                      Text(
                        'Preséntate',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _bioController,
                        maxLines: 5,
                        minLines: 4,
                        enabled: !_submitting,
                        decoration: const InputDecoration(
                          hintText:
                              'Describe quién eres y qué buscas (mínimo 20 caracteres).',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          _error!,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
                          ),
                        ),
                      ],
                      const SizedBox(height: 24),
                      Align(
                        alignment: Alignment.center,
                        child: SizedBox(
                          width: isWide ? 360 : double.infinity,
                          child: PrimaryButton(
                            label: 'Guardar y continuar',
                            loadingLabel: 'Guardando',
                            icon: Icons.check_circle,
                            loading: _submitting,
                            onPressed: _submitting ? null : _submit,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  void _togglePreset(String title) {
    setState(() {
      if (_selectedPresets.contains(title)) {
        _selectedPresets.remove(title);
      } else {
        _selectedPresets.add(title);
      }
    });
  }

  void _addCustomInterest() {
    final title = _customTitleController.text.trim();
    final description = _customDescController.text.trim();
    if (title.isEmpty || description.isEmpty) {
      setState(() {
        _error = 'Completa título y descripción del interés.';
      });
      return;
    }
    setState(() {
      _customInterests.add(
        UserInterest(title: title, description: description),
      );
      _customTitleController.clear();
      _customDescController.clear();
      _customInputExpanded = true;
      _error = null;
    });
  }

  void _removeCustomInterest(UserInterest interest) {
    setState(() {
      _customInterests.removeWhere(
        (i) =>
            i.title.toLowerCase() == interest.title.toLowerCase() &&
            i.description == interest.description,
      );
    });
  }

  void _toggleCustomInterestCard() {
    setState(() {
      _customInputExpanded = !_customInputExpanded;
    });
  }

  List<UserInterest> _collectInterests() {
    final interests = <UserInterest>[];

    for (final preset in _presets) {
      if (_selectedPresets.contains(preset.title)) {
        final controller = _presetControllers[preset.title];
        final description = controller?.text.trim();
        interests.add(
          UserInterest(
            title: preset.title,
            description: (description?.isNotEmpty ?? false)
                ? description!
                : preset.placeholder,
          ),
        );
      }
    }

    interests.addAll(_customInterests);

    final pendingTitle = _customTitleController.text.trim();
    final pendingDesc = _customDescController.text.trim();
    if (pendingTitle.isNotEmpty && pendingDesc.isNotEmpty) {
      interests.add(
        UserInterest(title: pendingTitle, description: pendingDesc),
      );
    }

    return interests;
  }

  Future<void> _submit() async {
    final interests = _collectInterests();
    final bio = _bioController.text;
    final validationError = validateProfileData(
      interests: interests,
      bio: bio,
      minBioLength: 20,
    );
    if (validationError != null) {
      setState(() {
        _error = validationError;
      });
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final profile = await widget.repository.completeProfile(
        session: widget.session,
        interests: interests,
        bio: bio.trim(),
      );
      if (!mounted) return;
      widget.onCompleted(profile);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceFirst('ProfileException: ', '');
        _submitting = false;
      });
    }
  }
}

class _CustomInterestCard extends StatelessWidget {
  const _CustomInterestCard({required this.interest, this.onDelete});

  final UserInterest interest;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      shape: RoundedRectangleBorder(
        side: BorderSide(color: colorScheme.secondary.withOpacity(0.4)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.push_pin_outlined, color: colorScheme.secondary),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    interest.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    interest.description,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
            if (onDelete != null)
              IconButton(
                onPressed: onDelete,
                tooltip: 'Eliminar',
                icon: const Icon(Icons.close),
              ),
          ],
        ),
      ),
    );
  }
}

class _CustomInterestInputCard extends StatelessWidget {
  const _CustomInterestInputCard({
    required this.selected,
    required this.titleController,
    required this.descController,
    required this.onToggle,
    required this.onAdd,
    required this.submitting,
  });

  final bool selected;
  final TextEditingController titleController;
  final TextEditingController descController;
  final VoidCallback onToggle;
  final VoidCallback onAdd;
  final bool submitting;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      elevation: selected ? 2 : 0,
      color: selected
          ? colorScheme.tertiaryContainer.withValues(alpha: 0.8)
          : colorScheme.surface,
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: selected ? colorScheme.secondary : colorScheme.outlineVariant,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            InkWell(
              borderRadius: BorderRadius.circular(8),
              onTap: onToggle,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Icon(
                      Icons.playlist_add,
                      color: selected
                          ? colorScheme.secondary
                          : colorScheme.onSurface,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Otro interés',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                    Icon(
                      selected
                          ? Icons.check_circle
                          : Icons.radio_button_unchecked,
                      color: selected
                          ? colorScheme.secondary
                          : colorScheme.outline,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Agrega cualquier interés que no veas en la lista.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: colorScheme.onSurfaceVariant,
              ),
            ),
            if (selected) ...[
              const SizedBox(height: 8),
              TextField(
                controller: titleController,
                enabled: !submitting,
                decoration: const InputDecoration(
                  labelText: 'Título',
                  hintText: 'Ej. Comunidad, Arte, Tech meetups',
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: descController,
                enabled: !submitting,
                decoration: const InputDecoration(
                  labelText: 'Descripción',
                  hintText: 'Describe brevemente este interés',
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: colorScheme.secondary,
                  ),
                  onPressed: submitting ? null : onAdd,
                  icon: const Icon(Icons.add),
                  label: const Text('Agregar interés'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _PresetCard extends StatelessWidget {
  const _PresetCard({
    required this.preset,
    required this.selected,
    required this.controller,
    required this.onToggle,
  });

  final _Preset preset;
  final bool selected;
  final TextEditingController controller;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      elevation: selected ? 2 : 0,
      color: selected
          ? colorScheme.secondaryContainer.withValues(alpha: 0.8)
          : colorScheme.surface,
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: selected ? colorScheme.secondary : colorScheme.outlineVariant,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onToggle,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    preset.icon,
                    color: selected
                        ? colorScheme.secondary
                        : colorScheme.onSurface,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      preset.title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  Icon(
                    selected
                        ? Icons.check_circle
                        : Icons.radio_button_unchecked,
                    color: selected
                        ? colorScheme.secondary
                        : colorScheme.outline,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                preset.placeholder,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: colorScheme.onSurfaceVariant,
                ),
              ),
              if (selected) ...[
                const SizedBox(height: 8),
                TextField(
                  controller: controller,
                  decoration: InputDecoration(
                    labelText: 'Describe este interés',
                    hintText: preset.placeholder,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _Preset {
  const _Preset({
    required this.title,
    required this.icon,
    required this.placeholder,
  });

  final String title;
  final IconData icon;
  final String placeholder;

  static const empty = _Preset(
    title: '_',
    icon: Icons.circle_outlined,
    placeholder: '',
  );
}

class _AccentChip extends StatelessWidget {
  const _AccentChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: colorScheme.secondaryContainer.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colorScheme.secondary.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: colorScheme.secondary),
          const SizedBox(width: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: colorScheme.secondary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}