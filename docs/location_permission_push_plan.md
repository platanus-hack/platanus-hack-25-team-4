# Background location permission push plan

Goal: maximize background location access (push users from “while in use” to “always”) while keeping the app functional only when minimum location is granted and continuously nudging to upgrade.

## Current signals from the codebase
- `geolocator` + `workmanager` + `shared_preferences` are wired; background jobs only run when permission is `always` (`circles/lib/core/background/location_reporting_worker.dart`).
- Permission flow already re-requests after `whileInUse` and shows a snackbar CTA to open settings (`circles/lib/main.dart`), but there is no dedicated gating UI/education to insist on background.
- Store policy declarations and UX for interval/status/foreground service are pending (`docs/background_location.md` tasks open).

## Task plan (prioritized)
- [ ] **Platform audit**: Re-check Android/iOS manifests/plists for “always” copy and background modes; ensure notification channel + `foregroundServiceType="location"` are set for continuous tracking. Update docs to reflect the exact strings.
- [ ] **Blocking gate for minimum permission**: Add a pre-permission screen that explains the feature and blocks core flows until at least “while using” is granted; if denied/deniedForever, force an interstitial with “Open settings” CTA.
- [ ] **Upgrade-to-always flow**: After the first successful foreground location (or on login), show an explainer modal and trigger `requestPermission()` again to surface the “Allow all the time/Always allow” sheet; if downgraded later, reshow the modal and deep link to settings.
- [ ] **Settings entry for status + interval**: Add a settings page section showing current permission state (while in use/always/denied), interval selector, and a button to open system settings; disable interval controls unless background permission is granted.
- [ ] **Foreground service option (Android)**: Implement a toggle to start a foreground service with a persistent notification for tighter intervals; fall back to WorkManager when off. Include rationale text in the notification (“Tracking for safety; tap to pause”).
- [ ] **Telemetry & copy**: Instrument permission outcomes (denied, while-in-use, always, downgraded) and worker successes/failures; refine copy to emphasize “app requires at least while using and works best with always”.
- [ ] **Policy updates**: Prepare Play Console/App Store background location declarations with the justification text used in-app.
- [ ] **QA matrix**: Real-device checks for Android (Allow all the time, backgrounded, reboot, OEM killers) and iOS (request upgrade path, background fetch/processing simulation, downgrade to while-in-use then recover).
- [ ] **Research**: Evaluate adding `flutter_background_service` or `flutter_background_geolocation` for more resilient background/foreground service management and OEM behavior notes (MIUI/ColorOS/EMUI). Document trade-offs and whether to adopt.

## Implementation notes to keep in mind
- Always request while-in-use first, then immediately request again to surface the “always” option; if `deniedForever`, only path is Settings.
- Gate scheduling of background jobs on `LocationPermission.always`; show a clear blocker when missing and prompt settings.
- Use persistent storage (`SharedPreferences`) to keep baseUrl/token/email/interval so background isolates can post even after app restarts.
- Communicate that iOS background cadence is best-effort; Android may require a foreground notification for reliability.

## Multiplatform implementation research (Android / iOS / Web)
- **Android**: Request `ACCESS_FINE_LOCATION` first, then `ACCESS_BACKGROUND_LOCATION` (API 29+) to surface “Allow all the time.” WorkManager runs 15m+ best-effort; for tighter or more reliable tracking, start a foreground service (`foregroundServiceType="location"`) with a persistent notification. Keep a Settings CTA for `deniedForever`, and consider OEM battery-optimization guidance (MIUI/ColorOS/EMUI). Telemetry downgrades so we can re-prompt.
- **iOS**: Add plist keys `NSLocationWhenInUseUsageDescription` and `NSLocationAlwaysAndWhenInUseUsageDescription` plus `UIBackgroundModes` (`location`, `fetch`, `processing`). Flow is two-step: `requestWhenInUseAuthorization()` then, at a moment of value, `requestAlwaysAuthorization()`; if downgraded to “While Using,” show an in-app explainer + Settings deep link. BGProcessing/BGAppRefresh are opportunistic; communicate that cadence is best-effort.
- **Web**: No true background location (geolocation not available in service workers). Only works while the page/PWA is open and focused; browser may throttle in background tabs. Provide a reduced mode: request foreground permission, poll while the tab is active, and show copy that continuous background tracking requires the mobile app.

## Platform-specific to-dos
- [ ] Android: verify manifest permissions include background + foreground service type; add notification channel + foreground service path for tighter intervals; add copy for OEM battery optimization exemptions.
- [ ] iOS: confirm plist strings are user-friendly and BGTask identifier matches `Workmanager` registration; ensure the app shows an “upgrade to always” modal before calling `requestAlwaysAuthorization()`.
- [ ] Web: gate background features; add an in-app notice that persistent tracking is unavailable on web and prompt users toward the mobile app for continuous reporting.

## Fresh web research (2025-02)
- Android docs (developer.android.com/training/location/permissions): background (`ACCESS_BACKGROUND_LOCATION`) is a separate grant shown only after “while in use” is allowed; targetSdk 30+ must request in a second step. Auto-reset can revoke location for unused apps, so re-prompt on return. Foreground services need `foregroundServiceType="location"` and a visible notification.
- Play Console policy (support.google.com/googleplay/android-developer/answer/9799150): background location requires a declaration form plus prominent in-app disclosure; Play may reject if background access is not essential or if you request it upfront without showing purpose.
- Apple Core Location (requestAlwaysAuthorization, iOS 13+): two-step flow—`requestWhenInUseAuthorization` first, then `requestAlwaysAuthorization` after demonstrating value. Users can downgrade to “While Using” or disable Precise Location; background updates require Precise and `UIBackgroundModes` entries.
- Web (MDN Geolocation API): no persistent background geolocation—works only while the page/PWA is open and often throttled in background tabs; service workers can’t access geolocation. Offer a “mobile app required for continuous tracking” notice.

Resulting follow-ups:
- [ ] Add in-app prominent disclosure screens before requesting background on Android (align with Play policy wording).
- [ ] Add downgrade detectors (Android auto-reset, iOS downgrade/precise toggle) and re-prompt flows.
- [ ] Web-only mode: disable background scheduling UI and show guidance to use mobile for continuous reporting.
