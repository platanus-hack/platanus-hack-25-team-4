# Flutter notes for Circles

## Current stack (Nov 2025)
- Flutter 3.38.3 (stable), Dart 3.10.1.
- Web renderers: `html` (smaller download) or `canvaskit` (better fidelity/animation); choose per target with `--web-renderer`.
- Hotfixes in 3.38: widget preview stability, Xcode 16 xcresult parser fixes, Android text-input fixes, Windows monitor info, Linux EGL rendering, skwasm GC tweaks on Web, `flutter doctor` no longer checks IDEs.

## Cross-platform best practices
- **Project hygiene**: Use env-specific entrypoints (`lib/main_dev.dart`, `lib/main_prod.dart`) with `--dart-define` for public config only. Keep secrets server-side.
- **Adaptive UI**: Favor `LayoutBuilder`, `MediaQuery`, `Flex`/`Expanded`, `AspectRatio`. Test text scaling and high contrast. Swap layouts for wide screens; avoid fixed sizes.
- **Platform awareness**: Prefer `kIsWeb` / `defaultTargetPlatform` over `Platform.isX` (which breaks on web). Guard non-web APIs. Use Material 3; selectively add Cupertino on iOS-feel screens.
- **Plugins**: Prefer packages with web implementations (`shared_preferences`, `url_launcher`, `path_provider`+web). Wrap platform services behind an interface so you can swap implementations.
- **Performance**: Mark widgets `const`, avoid rebuild-heavy trees, cache images, and defer heavy web-only code (deferred imports). Profile with DevTools per platform.
- **Accessibility & i18n**: Add `flutter_localizations` and `intl`; check contrast, semantics, and browser back-button behavior when using `Router`/`go_router`.
- **Web specifics**: Fill `web/manifest.json` name/short_name/icons, choose PWA strategy (`--pwa-strategy=offline-first` if needed), set `--base-href` when hosting under a subpath.
- **Android/iOS specifics**: Keep `compileSdk/targetSdk` current; declare permissions with rationale strings (Android `AndroidManifest.xml`, iOS `Info.plist`). Keep launch screens defined (Android theme, iOS storyboard).

## Responsive layout playbook (web + mobile)
- Breakpoints: <600px = phone (single column), 600–1024px = tablet/split view (two columns or rail + content), >1024px = wide web/desktop (nav rail or sidebar + max-width content ~1200px, centered).
- Sizing: Avoid fixed widths/heights; rely on `LayoutBuilder`, `MediaQuery`, `Flexible/Expanded`, `AspectRatio`, `FittedBox` only for short labels. Constrain max width on web so text lines stay readable.
- Navigation: Bottom nav or FAB on phones; nav rail/drawer for tablets; top app bar + rail/sidebar on wide web. Respect browser back button via `Router`/`go_router`.
- Typography & spacing: Use theme scales and spacing tokens; verify at text scale 1.1–1.5 and high-contrast modes. Keep touch targets ≥44x44dp and include hover/focus states on web.
- Orientation and safe areas: Use `SafeArea`, handle landscape with adaptive layouts instead of overflow; allow scroll (`SingleChildScrollView`/`CustomScrollView`) when height is constrained.
- Media: Serve responsive images (sized containers with `BoxFit.cover/contain`, `AspectRatio`), cache them, and avoid huge hero assets on mobile connections.
- Input & pointers: Support mouse/keyboard focus on web, gestures on touch; avoid hover-only interactions. Keep form fields keyboard-safe (`resizeToAvoidBottomInset`, proper padding).

## Recommended architecture
Feature-first layout with clear layers to keep platform quirks isolated:
- `lib/`
  - `core/` shared types, theme, routing, http/dio client, error handling.
  - `features/` per feature folder (e.g., `circles/`, `auth/`, `profile/`), each containing:
    - `presentation/`: widgets, screens, controllers/notifiers.
    - `application/`: use cases or services coordinating repositories.
    - `data/`: repositories + data sources (remote/local) and models/DTOs.
    - `domain/` (optional if you prefer Clean Architecture): entities/value objects and repository interfaces.
  - `l10n/` localization arb files and generated delegates.
  - `main_dev.dart`, `main_prod.dart`: wire env config and `ProviderScope`/`BlocProviders`.

### State management
- Use **Riverpod** (or Bloc if you prefer) for testable, platform-agnostic state. Keep UI in widgets; side effects in providers/use-cases. Avoid global singletons.

### Networking & storage
- HTTP client (e.g., `dio` or `http`) wrapped in a service; keep request/response models in `data/`.
- Storage abstractions with per-platform impls: `shared_preferences`/`hydrated` storage, and for files, pair `path_provider` with a web-safe alternative.

### Testing & CI
- Lint/analyze: `flutter analyze`. Unit/widget: `flutter test`. Integration: `integration_test` on Android/iOS devices/emulators and `flutter test --platform=chrome` for web.
- Add a small golden set only after theming stabilizes. Smoke-test navigation, back button on web, text scaling, and offline/PWA behavior.

### Build & release checklist
- Android: release `flutter build apk/appbundle`; sign via Play Console. iOS: archive in Xcode; ensure permission strings are set. Web: `flutter build web --release --source-maps` and pick renderer per host.
- Versioning: align `pubspec.yaml` `version` with Android `versionCode`/iOS `CFBundleVersion`. Keep flavors/schemes if you need staging/prod separation.

## Auth implementation (current)
- Configured via `assets/config/app_config.json` (`baseUrl`, `mockAuth`). Set `mockAuth` to `false` to hit `{baseUrl}/auth/login` (expects `token` or `access_token` in response). Leave `mockAuth: true` for offline dev.
- Email/password login persists session (email + token) with `shared_preferences` so returning users skip the form until they log out.
- Sign-up flow collects name/email/password (with confirmations), calls `{baseUrl}/auth/signup`, and logs in on success. Auth errors are parsed from API responses (`message`, `error`, or `errors` map) and shown inline on the UI.

## Visual reference (mockup colors)
Use `mockup/src/styles/globals.css` as the source of truth for palette. Key tokens:
- Primario: `#5B5FEE` (`--ac-primary`)
- Secundario: `#FF8A3D` (`--ac-secondary`)
- Acentos: `#34D1BF` (`--ac-accent-1`), `#FFD66B` (`--ac-accent-2`)
- Fondo claro: `#F6F7FC` (`--ac-bg-light`), fondo oscuro: `#171A2E` (`--ac-bg-dark`)
- Texto: primario `#1A1A1A`, secundario `#525866`
Reference file: `mockup/src/styles/globals.css`.
