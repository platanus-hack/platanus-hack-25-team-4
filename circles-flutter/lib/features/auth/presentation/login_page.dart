import 'package:flutter/material.dart';

import '../../../core/widgets/auth_layout.dart';
import '../../../core/widgets/primary_button.dart';
import '../data/auth_repository.dart';
import '../domain/auth_session.dart';
import 'signup_page.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({
    super.key,
    required this.authRepository,
    required this.onLoggedIn,
  });

  final AuthRepository authRepository;
  final ValueChanged<AuthSession> onLoggedIn;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _loading = false;
  bool _obscurePassword = true;
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
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
      final session = await widget.authRepository
          .login(_emailController.text, _passwordController.text);
      widget.onLoggedIn(session);
    } catch (e) {
      setState(() {
        _error = e.toString().replaceFirst('AuthException: ', '');
      });
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      body: AuthLayout(
        title: 'Bienvenido a Circles',
        subtitle: 'Inicia sesión con tu correo y contraseña.',
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.username],
                decoration: const InputDecoration(
                  labelText: 'Correo',
                  prefixIcon: Icon(Icons.mail_outline),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'El correo es obligatorio';
                  }
                  final trimmed = value.trim();
                  final emailRegex = RegExp(
                    r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$',
                  );
                  if (!emailRegex.hasMatch(trimmed)) {
                    return 'Ingresa un correo válido';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                autofillHints: const [AutofillHints.password],
                decoration: InputDecoration(
                  labelText: 'Contraseña',
                  prefixIcon: const Icon(Icons.lock_outline),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                    ),
                    tooltip:
                        _obscurePassword ? 'Mostrar contraseña' : 'Ocultar contraseña',
                    onPressed: () =>
                        setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'La contraseña es obligatoria';
                  }
                  if (value.length < 8) {
                    return 'La contraseña debe tener al menos 8 caracteres';
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
                label: 'Ingresar',
                loadingLabel: 'Iniciando sesión',
                icon: Icons.login,
                loading: _loading,
                onPressed: _submit,
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: _loading ? null : () => _openSignUp(context),
                child: const Text('¿No tienes cuenta? Regístrate'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _openSignUp(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => SignUpPage(
          authRepository: widget.authRepository,
          onSignedUp: widget.onLoggedIn,
        ),
      ),
    );
  }
}
