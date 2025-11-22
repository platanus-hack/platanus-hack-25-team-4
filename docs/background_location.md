# Background location implementation plan

Goal: upgrade from foreground-only location access to periodic background reporting that survives app closes, aligns with Play/App Store policies, and keeps user control clear.

## Task list (status)
- [x] Dependencies present (`geolocator`, `workmanager`, `shared_preferences` in `pubspec.yaml`).
- [x] Android manifest permissions + `foregroundServiceType="location"` on `MainActivity`.
- [x] iOS plist keys (`NSLocationWhenInUseUsageDescription`, `NSLocationAlwaysAndWhenInUseUsageDescription`, `UIBackgroundModes`, `BGTaskSchedulerPermittedIdentifiers`).
- [x] iOS AppDelegate registers the periodic BG task via `WorkmanagerPlugin.registerPeriodicTask`.
- [x] Background worker/scheduler implemented (`lib/core/background/location_reporting_worker.dart`) and initialized in `main.dart`; tokens/baseUrl persisted to prefs.
- [ ] UX surface for interval selection + rationale/copy explaining “always” and best-effort cadence on iOS.
- [x] Prominent disclosure before background request (Play policy) + downgrade/auto-reset detection and settings CTA (Android/iOS).
- [ ] Store declarations (Play Console/App Store) updated with background location purpose.
- [x] Web notice: persistent background tracking unavailable on web/PWA; guide users to mobile app.
- [ ] Device validation: Android (Allow all the time, backgrounded, >15m), iOS (simulate background fetch/BG processing), reboot/resume tests.

## How background location works (platform constraints)
- Android: background requires `ACCESS_BACKGROUND_LOCATION` and is only shown after the user grants while-in-use. Periodic work is best-effort; WorkManager runs with a 15m+ floor. Foreground services with a persistent notification are needed for tighter intervals.
- iOS: “Always” is only offered after “While Using”. BGProcessing/BGAppRefresh are system scheduled (can be infrequent). Background modes + plist keys must be present; Apple will reject if justification is weak.
- Web: no true background geolocation; location only works while the page/PWA is open and may be throttled in background tabs. Service workers cannot access geolocation.

## Recommended stack for this app
- `geolocator` for permission checks and coordinates (foreground + background capable).
- `workmanager` to run a Dart task that fetches and posts location on both platforms.
- `shared_preferences` to store auth token, email, base URL, and chosen interval so the background isolate can read them.

## Implementation steps
1) **Dependencies**  
   - Ensure `geolocator`, `workmanager`, and `shared_preferences` are in `pubspec.yaml`; run `flutter pub get`.

2) **Platform configuration**  
   - **Android (`android/app/src/main/AndroidManifest.xml`)**  
     - Add permissions under `<manifest>`: `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `ACCESS_BACKGROUND_LOCATION`, `FOREGROUND_SERVICE`, `RECEIVE_BOOT_COMPLETED`.  
     - Set `android:foregroundServiceType="location"` on `MainActivity` (or on your foreground service if you add one).  
     - Runtime flow: request while-in-use first, then background, otherwise the “Allow all the time” option will not appear on Android 10+.  
   - **iOS (`ios/Runner/Info.plist`)**  
     - Keys: `NSLocationWhenInUseUsageDescription`, `NSLocationAlwaysAndWhenInUseUsageDescription` with honest copy; add `UIBackgroundModes` entries `location`, `fetch`, `processing`.  
     - For Workmanager iOS: add `BGTaskSchedulerPermittedIdentifiers` (e.g., `com.example.circles.location.periodic`) and register it in `AppDelegate` via `WorkmanagerPlugin.registerPeriodicTask`. Deployment target 14+.  
     - Expect iOS to run tasks at its discretion; communicate that frequency is best-effort.

3) **Permission flow in Dart**  
   - Keep requesting while-in-use first. If granted, immediately request “always” so Android shows the full-time option and iOS can present the upgrade sheet.  
   - Gate scheduling on `LocationPermission.always`; if not granted, fall back to foreground-only behavior and surface a message.  
   - Detect downgrades/auto-reset: if permission falls back to while-in-use/denied on subsequent checks, show a blocking explainer and deep link to settings before resuming background work. Implemented in `main.dart` on app resume with a Settings CTA.

4) **Background worker (Dart)**  
   - Use a `@pragma('vm:entry-point')` callback (see `lib/core/background/location_reporting_worker.dart`) that:  
     - Reads base URL, auth token, and email from `SharedPreferences`.  
     - Checks `Geolocator.isLocationServiceEnabled()` and permission `always`.  
     - Calls `Geolocator.getCurrentPosition()` and POSTs to `/ubicaciones` with `lat`, `lng`, `recordedAt`, and `email`.  
     - Returns `false` on network/location failures so Workmanager can retry.  
     - If no backend config/token is present, it still captures the coordinate and logs it to console for testing.  
   - Keep the task name stable (e.g., `com.example.circles.location.periodic`).

5) **Scheduling lifecycle**  
   - After login, store creds/base URL in prefs and call `Workmanager.initialize` once, then `registerPeriodicTask` with the user-selected interval (clamped to 15–180 minutes).  
   - On logout, clear the stored creds and `cancelByUniqueName` to stop background sends.  
   - Persist the chosen interval in prefs and re-register the task when the interval changes.

6) **User controls & UX**  
   - Explain why background access is needed and that iOS cadence is best-effort. Present a prominent disclosure before requesting background (Android Play requirement). Implemented as a blocking modal in `main.dart` before requesting background permission.  
   - Provide a selector (slider/dropdown) for “send my location every N minutes” within a sensible range (15–180).  
   - Surface status/error states (e.g., location services off, permission denied) and a link to system settings to enable background access; include copy to recover from downgrades/auto-reset.
   - Web: disable background controls and show guidance that continuous tracking requires the mobile app. Currently shows a notice when starting reporting on web; still need to disable background-only controls when added.

7) **Policy & rollout**  
   - Update Play Console location declaration (background purpose) and App Store “Always” justification.  
   - Ship with analytics/logs to measure success/fail counts of the worker and permission grants.

8) **Testing checklist**  
   - Android device: grant “Allow all the time”, background the app, wait >15m, verify backend receives points; reboot to confirm rescheduling.  
   - iOS device/simulator: use “Simulate Background Fetch”; verify plist keys and BGTask registration; expect sparse runs.  
   - Deny/disable location to ensure graceful handling; re-enable to confirm recovery.  
   - Logout/login to confirm tasks stop/start and use the latest creds/interval.

## Current code touchpoints
- `lib/core/background/location_reporting_worker.dart`: contains the Workmanager dispatcher, permission helper, and scheduler; ensure it’s wired in `main.dart` after auth and on logout.  
- Verify `baseUrl` and tokens are set into `SharedPreferences` so the background isolate can post while the app is closed.

## Minimal modifications required for “Always allow” to work
- Keep/verify platform permissions and background modes (Android manifest + iOS Info.plist) and BGTask registration in AppDelegate.
- Ensure the permission flow asks for while-in-use first, then upgrades to “always” (`LocationPermissionService.ensureBackgroundPermission`).
- Store auth/baseUrl/interval in `SharedPreferences` before scheduling; Workmanager reads them in the background isolate.
- Invoke scheduling after login and cancel on logout so the periodic task runs only for authenticated users.
- Add a small UX entry point to set interval and explain why “always” is requested (pending).
