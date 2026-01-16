# WFM Pro Mobile Walkthrough

## Overview
We have generated a Flutter project structure in `flutter_project_assets/`.

## Prerequisites
1.  **Flutter SDK**: Ensure you have Flutter installed (`flutter --version`).
2.  **Existing Project**: Create a new Flutter project if you haven't already:
    ```bash
    flutter create wfm_mobile
    ```

## Installation
1.  Navigate to your generated assets:
    ```bash
    cd c:\Code\wfm-pro\flutter_project_assets
    ```
2.  Copy the `lib` folder into your Flutter project's root, overwriting the existing `lib`.

3.  Update your `pubspec.yaml` in the Flutter project to include these dependencies:
    ```yaml
    dependencies:
      flutter:
        sdk: flutter
      http: ^1.1.0
      shared_preferences: ^2.2.0
      intl: ^0.18.1
    ```

4.  Run `flutter pub get`.

## Running
1.  Connect a device or start an emulator.
2.  Run:
    ```bash
    flutter run
    ```

## Usage
1.  **Login Screen**:
    *   **Workspace**: Enter your tenant subdomain (e.g., `tenant1`).
    *   **Username/Password**: Your WFM Pro credentials.
    *   *Note*: The app attempts to connect to `https://tenant1.wfm-pro.com`. Ensure DNS is working!

2.  **Dashboard**: Shows your next shift and notifications.
3.  **Schedule**: Shows your full shift list.
