# BIE Android PDF submission foundation

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

The app now offers **Choose PDF** through Android's system document picker
(`OpenDocument`, `application/pdf`). It requests no storage permission. A selected
file is streamed into a temporary app-cache file with a strict 25 MiB limit;
SHA-256 and size are computed during that pass. The original filename is never
used as the cache filename. The user can submit only after both backend and
Document Intelligence connectivity checks pass. The app streams the raw PDF to
`POST /v1/jobs/document-inspection`, validates the persistent job response and
source hash, and shows the returned job ID/status. An accepted submission removes
the staged file. Failed network attempts can be retried within the Activity
session with the same idempotency key; selecting a new file creates a new key.
No restart-resumable upload is claimed. Android does not run backend workers.

## What this milestone can prove

- Android source and resource structure
- GitHub CI compilation with lint and JVM unit tests
- Debug APK creation and an APK SHA-256 receipt
- A launchable foundation with an explicit health and capability check
- PDF selection, bounded staging, and persistent-job submission contracts

The earlier Android foundation was physically launch-validated. Network
connectivity on a physical device remains a separate acceptance step.

## What this milestone does not prove

- Document Intelligence runtime or real-book processing
- Automatic job polling, result retrieval/display, or backend worker control
- Physical-device network connectivity
- Physical-device PDF upload acceptance
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

The dedicated PDF submission workflow builds a debug APK, runs lint and JVM
tests, checks merged debug/release manifest policies, and exercises synthetic
persistent-job submission, idempotent replay, and conflict over a local loopback
API. Authentication and public deployment remain absent. No product acceptance
is claimed.
