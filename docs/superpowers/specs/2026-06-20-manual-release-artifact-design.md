# Manual release artifact design

## Goal

Provide a simple GitHub-based way to generate a full installable Android APK on demand, without requiring a tagged release every time.

## User outcome

When the user wants an APK, they open GitHub Actions, manually start a workflow, wait for the job to finish, then download a release APK artifact from the workflow run.

## Scope

In scope:
- Add a new GitHub Actions workflow triggered by `workflow_dispatch`
- Build a signed `release APK`
- Upload the built APK as an Actions artifact
- Reuse existing signing secrets already referenced by the repository

Out of scope:
- Publishing a GitHub Release
- Creating or pushing version tags
- Changing the existing release workflow
- Play Store publishing

## Existing repo context

- `ci.yml` already builds `assembleDebug` for pull requests
- `release.yml` already builds signed release outputs on version tags
- `release.yml` already depends on `KEYSTORE_BASE64` and `SIGNING_PASSWORD`

This means the repository already has most of the release build logic. The missing capability is an on-demand workflow that produces a downloadable full APK artifact without creating a formal release.

## Approaches considered

### Recommended: separate manual release-artifact workflow

Add a new workflow dedicated to on-demand full APK generation.

Pros:
- Keeps CI, release publishing, and manual artifact generation separate
- Reuses the existing release signing model
- Does not require a new tag
- Easy for the user to run only when needed

Cons:
- Adds one more workflow file

### Alternative: extend the existing release workflow

Allow the tag-based release workflow to also run manually.

Pros:
- Less duplicated setup

Cons:
- Mixes two different intents: formal releases and ad hoc APK generation
- Makes the release workflow harder to reason about

### Alternative: build a debug artifact manually

Generate `app-debug.apk` instead of a signed release APK.

Pros:
- Simpler

Cons:
- Does not match the requirement for a full version artifact

## Design

Create a new workflow file, for example `manual-release-artifact.yml`, with:
- trigger: `workflow_dispatch`
- Java 21 setup
- Gradle setup
- keystore decode step
- `./gradlew assembleRelease`
- artifact upload for `app/build/outputs/apk/release/app-release.apk`

The workflow should produce a clearly named artifact such as `scrib-release-apk`.

## Data and secrets

The workflow will rely on the existing repository secrets:
- `KEYSTORE_BASE64`
- `SIGNING_PASSWORD`

No new secret format is required if the current release workflow is already valid.

## Error handling

- If signing secrets are missing or invalid, the workflow fails clearly during keystore decode or release build
- If Gradle dependency resolution fails, the workflow fails in the build step
- If the output APK path changes, the artifact upload step fails and should be updated to match the real output path

## Verification

Success means:
- The workflow is visible under GitHub Actions
- The user can manually run it
- The run completes successfully
- A downloadable release APK artifact is attached to the run

## Recommendation

Implement a new manual workflow for signed release APK artifacts and leave the existing tag-based release workflow unchanged.
