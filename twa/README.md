# Job Hunter Pro — Android APK (TWA wrapper)

This wraps the deployed PWA at
`https://job-hunter-pro-1087899531014.us-central1.run.app` into an installable
Android APK using a Trusted Web Activity. The APK is a thin shell that loads the
live site fullscreen — the Flask backend still runs on Cloud Run, not on the phone.

## Get the APK without installing anything (recommended)

Every push that touches `twa/` triggers the **Build Android APK** GitHub Action.
Open the repo's **Actions** tab → latest "Build Android APK" run → download the
`job-hunter-pro-apk` artifact. Unzip → `app-debug.apk` → open it with your
Android package installer.

You can also trigger it by hand: Actions tab → Build Android APK → Run workflow.

## Build locally (if you have the Android SDK + JDK 17)

```
cd twa
gradle assembleDebug
# APK lands at: twa/app/build/outputs/apk/debug/app-debug.apk
```

## Fullscreen (no address bar)

The debug build is signed with the Android debug key. To verify the app↔site link
so Chrome drops the URL bar, take the `SHA256:` fingerprint printed in the Action
log (or from `keytool -list -v -keystore ~/.android/debug.keystore -storepass
android -alias androiddebugkey`) and set it on Cloud Run:

```
gcloud run services update job-hunter-pro --region us-central1 \
  --update-env-vars TWA_SHA256_FINGERPRINT="<paste fingerprint>",TWA_PACKAGE_NAME=com.mjmichaelware.jobhunterpro
```

The `/.well-known/assetlinks.json` route already serves it once those vars are set.
Without this step the APK still installs and runs — just with a thin URL bar.
