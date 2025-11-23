## Perfil: tareas para completar perfil tras login/signup

- Alinear contrato con backend: `GET /me` devuelve `profileCompleted`, `interests`, `bio`; `POST /profile` acepta `{ interests: [{title, description}], bio }` y marca `profileCompleted=true`. Usar bearer token de `AuthSession.token` y `baseUrl` de `app_config.json`; mantener `mockAuth` con respuestas simuladas.
- Data/domain: crear `UserProfile` y `ProfileApiClient` (http + headers + manejo de errores similar a `AuthApiClient`), más `ProfileRepository` con `fetchCurrentUser()` y `completeProfile(...)`. Incluir modo `mockAuth`.
- Estado y routing: instanciar `ProfileRepository` en `main.dart`; tras login/signup o sesión guardada, llamar `fetchCurrentUser`. Si `profileCompleted` es `false`, mostrar wizard antes del `AuthenticatedShell`; si es `true`, continuar normal.
- UI wizard: nueva pantalla `profile_wizard_page.dart` con layout responsivo (`LayoutBuilder`/`Wrap`/`SingleChildScrollView`). Tarjetas de intereses por defecto (título + ícono) que al seleccionarse muestran input con placeholder de ejemplo:
  - Trabajo (briefcase): “Busco / Ofrezco trabajo, soy dev y busco startups”
  - Videojuegos (sports_esports): “Juego Valorant, LoL, etc”
  - Deporte (directions_run): “Juego Padel, corro, etc”
  - Literatura (menu_book): “Me encantan los libros de ciencia ficción”
  - Salir a tomar algo (local_bar): “Me interesa ir a un bar...”
  - Buscar pareja (favorite_border): “Busco una persona que...”
  Incluir campo para “Otro interés” (título + descripción) y un textarea para “Preséntate”.
- Validación + envío: requerir mínimo un interés (incluye custom) y bio ≥ 20 caracteres; mostrar errores inline. Botón de enviar deshabilitado con loading mientras se llama a `completeProfile`; en éxito, marcar `profileCompleted=true` y navegar al shell.
- Pruebas/manual: agregar test de validación (p.ej. en `test/profile_wizard_validator_test.dart`). Verificar login/signup → wizard cuando falta perfil; usuarios completos saltan wizard; envío exitoso entra al shell; layouts correctos en web/móvil; `mockAuth` funciona offline.
