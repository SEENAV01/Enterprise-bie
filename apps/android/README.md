# BIE Android foundation and API connectivity

This directory contains the first Android productization foundation for My Book
Intelligence Engine. Canonical BIE engines remain under `bie/`; this application
does not duplicate or rewrite them.

The foundation now includes an explicit **Check connection** action. It calls
the canonical BIE API's `GET /healthz` and `GET /v1/capabilities` endpoints and
marks the engine and Document Intelligence connected only when both responses
match the governed contract. The initial state remains disconnected.

Configure the API base URL at build time with `-PbieApiBaseUrl=https://host`
or `BIE_ANDROID_API_BASE_URL`. The Gradle property takes precedence. The default
is empty; an unconfigured app makes no network request and shows **Not
configured**. No machine IP address is embedded in source. The client uses
`HttpURLConnection`, 5-second connect and 10-second read timeouts, disabled
redirects, a 256 KiB response limit, and pinned kotlinx.serialization JSON
1.10.0 for typed response parsing. It never displays raw server responses.

Release builds disable cleartext HTTP. Only the debug manifest enables it for
local development through loopback, ADB reverse, or a development LAN. The
manifest requests `INTERNET` and no Android runtime permissions. This is not a
public deployment configuration.

## What this milestone can prove

- Android source and resource structure
- GitHub CI compilation with lint and JVM unit tests
- Debug APK creation and an APK SHA-256 receipt
- A launchable foundation with an explicit health and capability check

The earlier Android foundation was physically launch-validated. Network
connectivity on a physical device remains a separate acceptance step.

## What this milestone does not prove

- Document Intelligence runtime or real-book processing
- PDF selection, upload, job submission/polling, or result display on Android
- Physical-device network connectivity
- Authentication or public backend deployment
- Media or video generation
- Audio generation or playback
- Playable revision games
- Product or end-to-end acceptance

## Pinned build baseline

- Android Gradle Plugin: 9.4.0
- CI Gradle: 9.6.0 (installed by the official Gradle GitHub Action)
- CI JDK: Temurin 17
- Kotlin/Compose Compiler plugin: 2.4.10
- Compile SDK: API 37.0
- `targetSdk`: 37
- `minSdk`: 26
- Compose BOM: 2026.09.00
- Activity Compose: 1.13.0

No Gradle wrapper is committed in this milestone. The separate Android CI
workflow installs the pinned Gradle version explicitly.

The dedicated connectivity workflow builds a debug APK, runs lint and JVM
tests, checks merged debug/release manifest policies, and compares the live
canonical API responses to the shared Android contract fixture over loopback.
The backend remains a local-development service. No product acceptance is
claimed.
