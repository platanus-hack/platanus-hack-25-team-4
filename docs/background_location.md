# Background location reporting

How to send the user location to the backend every _N_ minutes (configurable by the user), continuing while the app is in background or closed.

## Research recap
- `geolocator` provides location access but, per its README, background updates need explicit permissions (`ACCESS_BACKGROUND_LOCATION`) and aren’t processed by the plugin unless you drive them yourself (e.g., via a background task).
- `workmanager` runs Dart in the background on Android (reliable, min 15 min interval) and iOS (system-controlled frequency; requires iOS 14+, background modes). Quickstart docs outline BGTaskScheduler setup for periodic work with custom frequency.
- iOS background execution is system-controlled. Background Fetch can run as rarely as ~1x/day; BGProcessing tasks have a 15+ minute floor and only run when the system allows. We should set expectations in the UI.

## Proposed stack
- `geolocator` for permissions + coordinates.
- `workmanager` for periodic background execution.
- Reuse `http` + `CredentialsStorage` to attach the auth token; persist the chosen interval in `SharedPreferences`.
- Start the worker right after login; cancel it on logout.

## Step-by-step
1) **Add dependencies**
   - In `circles/pubspec.yaml` add:
     ```yaml
     dependencies:
       geolocator: ^12.0.0
       workmanager: ^0.8.0
     ```
   - Run `flutter pub get`.

2) **Platform setup**
   - **Android (`android/app/src/main/AndroidManifest.xml`)**
     - Add permissions as direct children of `<manifest>`:
       ```xml
       <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
       <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
       <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
       <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
       <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
       ```
     - If you keep a long-running stream, mark the activity for location foreground services:
       ```xml
       <activity
         android:name=".MainActivity"
         ...
         android:foregroundServiceType="location">
       ```
     - Runtime flow on Android 10+: request `whileInUse` first, then `always` so users see the system “Allow all the time” option.
   - **iOS (`ios/Runner/Info.plist`)**
     - Minimum deployment target 14.0+ (per Workmanager).
     - Add permission texts:
       ```xml
       <key>NSLocationWhenInUseUsageDescription</key>
       <string>Necesitamos tu ubicación para mostrarte personas cercanas.</string>
       <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
       <string>Seguimos enviando tu ubicación cada cierto tiempo incluso en segundo plano.</string>
       ```
     - Background modes (Capabilities in Xcode or directly in Info.plist):
       ```xml
       <key>UIBackgroundModes</key>
       <array>
         <string>location</string>
         <string>fetch</string>
         <string>processing</string>
       </array>
       ```
     - For Workmanager periodic tasks with custom frequency (BGTaskScheduler):
       ```xml
       <key>BGTaskSchedulerPermittedIdentifiers</key>
       <array>
         <string>com.circles.location.periodic</string>
       </array>
       ```
       And in `ios/Runner/AppDelegate.swift`:
       ```swift
       import workmanager_apple

       // In didFinishLaunchingWithOptions
       WorkmanagerPlugin.registerPeriodicTask(
         withIdentifier: "com.circles.location.periodic",
         frequency: NSNumber(value: 15 * 60) // 15 min minimum
       )
       ```
     - Set user expectations: iOS will not honor exact minute-level schedules.

3) **Permissions helper (Dart)**
   - Create `lib/core/location/location_service.dart` with a method like:
     ```dart
     import 'package:geolocator/geolocator.dart';

     class LocationService {
       Future<Position?> ensurePermissionAndFetch() async {
         if (!await Geolocator.isLocationServiceEnabled()) return null;

         var permission = await Geolocator.checkPermission();
         if (permission == LocationPermission.denied) {
           permission = await Geolocator.requestPermission();
         }
         if (permission == LocationPermission.deniedForever ||
             permission == LocationPermission.denied) {
           return null;
         }

         // Ask for "always" when available so Android 10+/iOS allow background use.
         if (permission == LocationPermission.whileInUse) {
           final upgraded = await Geolocator.requestPermission();
           if (upgraded == LocationPermission.denied ||
               upgraded == LocationPermission.deniedForever) {
             return null;
           }
         }

         return Geolocator.getCurrentPosition(
           desiredAccuracy: LocationAccuracy.high,
         );
       }
     }
     ```

4) **Background worker (Dart)**
   - Add `lib/core/background/location_reporting_worker.dart`:
     ```dart
     import 'dart:convert';
     import 'package:geolocator/geolocator.dart';
     import 'package:http/http.dart' as http;
     import 'package:shared_preferences/shared_preferences.dart';
     import 'package:workmanager/workmanager.dart';

     const locationTaskName = 'com.circles.location.report';

     @pragma('vm:entry-point')
     void locationCallbackDispatcher() {
       Workmanager().executeTask((task, inputData) async {
         if (task != locationTaskName && task != Workmanager.iOSBackgroundTask) {
           return Future.value(true);
         }

         final prefs = await SharedPreferences.getInstance();
         final token = prefs.getString('auth_token');
         final email = prefs.getString('auth_email');
         final baseUrl = prefs.getString('api_base_url');
         if (token == null || baseUrl == null) return Future.value(false);

         final pos = await Geolocator.getCurrentPosition(
           desiredAccuracy: LocationAccuracy.high,
         );

         final body = {
           'email': email,
           'lat': pos.latitude,
           'lng': pos.longitude,
           'recordedAt': DateTime.now().toUtc().toIso8601String(),
         };

         final response = await http.post(
           Uri.parse(baseUrl).resolve('/ubicaciones'),
           headers: {
             'Content-Type': 'application/json',
             'Authorization': 'Bearer $token',
           },
           body: jsonEncode(body),
         );

         return response.statusCode >= 200 && response.statusCode < 300;
       });
     }
     ```
   - Store `api_base_url` in prefs once (e.g., when loading `AppConfig`) so the background isolate doesn’t need DI.

5) **Initialize and schedule after login**
   - In `lib/main.dart` (or a new app controller), after a successful login:
     ```dart
     await Workmanager().initialize(locationCallbackDispatcher);
     await Workmanager().registerPeriodicTask(
       locationTaskName,
       locationTaskName,
       existingWorkPolicy: ExistingPeriodicWorkPolicy.update,
       frequency: Duration(minutes: userIntervalMinutes.clamp(15, 180)),
       initialDelay: const Duration(minutes: 1),
     );
     ```
   - On logout, call `Workmanager().cancelByUniqueName(locationTaskName);`.

6) **Persist and expose the interval**
   - Add a small params screen (e.g., under Perfil) with a `Slider`/`DropdownButton` letting users choose every 15–180 minutes.
   - Save to `SharedPreferences` (`location_interval_minutes`) and re-register the periodic task with `ExistingPeriodicWorkPolicy.update` when it changes.
   - Show copy that iOS execution is best-effort and may be less frequent.

7) **API contract**
   - Decide/align with backend on an endpoint like `POST /ubicaciones` with body `{ lat, lng, recordedAt }`. Include auth token in `Authorization: Bearer`.
   - Consider deduplicating on the backend by `(userId, recordedAt rounded to interval)`.

8) **Testing checklist**
   - **Android emulator/device:** grant “Allow all the time”, lock the screen, wait >15 minutes, check server logs or add temporary logging inside the worker. Reboot device to confirm tasks reschedule (needs RECEIVE_BOOT_COMPLETED).
   - **iOS simulator/device:** enable Background Fetch in Debug > Simulate Background Fetch, then test BGProcessing by running via `xcrun simctl` commands; verify Info.plist keys and AppDelegate registration.
   - Disable location services and confirm the worker exits gracefully and resumes once enabled.
   - Logout/login flow cancels/restarts the worker as expected.

## Notes
- Keep background work lightweight (<30s on iOS). If the backend is down, return `false` so Workmanager retries.
- If you need tighter-than-15-minute Android updates, switch to a foreground location stream with a persistent notification; that is outside Workmanager and requires UX approval.
- For iOS, if Apple rejects background location, fall back to Background Fetch only (less frequent) and communicate limitations in-app.
