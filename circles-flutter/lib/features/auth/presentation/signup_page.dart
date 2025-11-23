import 'package:flutter/material.dart';

import '../../../core/widgets/app_logo.dart';
import '../../../core/widgets/auth_layout.dart';
import '../../../core/widgets/primary_button.dart';
import '../data/auth_repository.dart';
import '../domain/auth_session.dart';

class SignUpPage extends StatefulWidget {
  const SignUpPage({
    super.key,
    required this.authRepository,
    required this.onSignedUp,
  });

  final AuthRepository authRepository;
  final ValueChanged<AuthSession> onSignedUp;

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _emailConfirmController = TextEditingController();
  final _passwordController = TextEditingController();
  final _passwordConfirmController = TextEditingController();
  bool _loading = false;
  bool? _obscurePassword = true;
  bool? _obscurePasswordConfirm = true;
  String? _error;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _emailConfirmController.dispose();
    _passwordController.dispose();
    _passwordConfirmController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final form = _formKey.currentState;
    if (form == null || !form.validate()) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final session = await widget.authRepository.signUp(
        name: _nameController.text,
        email: _emailController.text,
        password: _passwordController.text,
      );
      widget.onSignedUp(session);
      if (mounted) {
        // Close the signup flow so the root navigator rebuilds with the profile wizard.
        Navigator.of(context).popUntil((route) => route.isFirst);
      }
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('AuthException: ', ''));
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  String? _validateEmail(String? value) {
    if (value == null || value.trim().isEmpty) return 'El correo es obligatorio';
    final trimmed = value.trim();
    final emailRegex = RegExp(r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$');
    if (!emailRegex.hasMatch(trimmed)) return 'Ingresa un correo válido';
    return null;
  }

  String? _validatePassword(String? value) {
    if (value == null || value.isEmpty) return 'La contraseña es obligatoria';
    if (value.length < 8) return 'La contraseña debe tener al menos 8 caracteres';
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const AppLogo(text: 'Circles - Crear cuenta'),
      ),
      body: AuthLayout(
        title: 'Únete a Circles',
        subtitle: 'Crea una cuenta para comenzar.',
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _nameController,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Nombre',
                  prefixIcon: Icon(Icons.person_outline),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'El nombre es obligatorio';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                decoration: const InputDecoration(
                  labelText: 'Correo',
                  prefixIcon: Icon(Icons.mail_outline),
                ),
                validator: _validateEmail,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailConfirmController,
                keyboardType: TextInputType.emailAddress,
                // Leave autofill off to avoid duplicate email input IDs on web.
                decoration: const InputDecoration(
                  labelText: 'Confirmar correo',
                  prefixIcon: Icon(Icons.mark_email_read_outlined),
                ),
                validator: (value) {
                  final error = _validateEmail(value);
                  if (error != null) return error;
                  if (value!.trim() != _emailController.text.trim()) {
                    return 'Los correos no coinciden';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                obscureText: _obscurePassword ?? true,
                autofillHints: const [AutofillHints.newPassword],
                decoration: InputDecoration(
                  labelText: 'Contraseña',
                  prefixIcon: const Icon(Icons.lock_outline),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword ?? true
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                    ),
                    tooltip:
                        (_obscurePassword ?? true)
                            ? 'Mostrar contraseña'
                            : 'Ocultar contraseña',
                    onPressed: () => setState(
                      () => _obscurePassword = !(_obscurePassword ?? true),
                    ),
                  ),
                ),
                validator: _validatePassword,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordConfirmController,
                obscureText: _obscurePasswordConfirm ?? true,
                autofillHints: const [AutofillHints.newPassword],
                decoration: InputDecoration(
                  labelText: 'Confirmar contraseña',
                  prefixIcon: const Icon(Icons.lock_person_outlined),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePasswordConfirm ?? true
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                    ),
                    tooltip: (_obscurePasswordConfirm ?? true)
                        ? 'Mostrar contraseña'
                        : 'Ocultar contraseña',
                    onPressed: () => setState(
                      () =>
                          _obscurePasswordConfirm = !(_obscurePasswordConfirm ?? true),
                    ),
                  ),
                ),
                validator: (value) {
                  final error = _validatePassword(value);
                  if (error != null) return error;
                  if (value != _passwordController.text) {
                    return 'Las contraseñas no coinciden';
                  }
                  return null;
                },
                onFieldSubmitted: (_) => _submit(),
              ),
              const SizedBox(height: 12),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8.0),
                  child: Text(
                    _error!,
                    style: TextStyle(
                      color: theme.colorScheme.error,
                    ),
                  ),
                ),
              const SizedBox(height: 8),
              PrimaryButton(
                label: 'Crear cuenta',
                loadingLabel: 'Creando cuenta',
                icon: Icons.person_add_alt_1,
                loading: _loading,
                onPressed: _submit,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
