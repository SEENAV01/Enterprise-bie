# BIE Android foundation

This directory contains the first Android productization foundation for My Book
Intelligence Engine. Canonical BIE engines remain under `bie/`; this application
does not duplicate or rewrite them.

The current milestone provides a launchable, fail-closed application shell. It
does not connect to a BIE API, backend, or Document Intelligence runtime, and it
does not simulate successful PDF or book processing.

## What this milestone can prove

- Android source and resource structure
- GitHub CI compilation with lint and JVM unit tests
- Debug APK creation and an APK SHA-256 receipt
- A launchable foundation for later physical-device validation

Physical-device launch remains pending until a user installs the CI-built APK.

## What this milestone does not prove

- Document Intelligence runtime or real-book processing
- Backend or API connectivity
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
