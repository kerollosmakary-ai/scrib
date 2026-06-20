# Manual Release Artifact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manual GitHub Actions workflow that builds a signed release APK and uploads it as a downloadable artifact on demand.

**Architecture:** Add one new workflow file under `.github/workflows` that reuses the existing release signing pattern from `release.yml` but changes the trigger to `workflow_dispatch` and the output to an Actions artifact instead of a GitHub Release. Keep the existing PR CI and tag-based release flow unchanged, and document how to run the new workflow in `README.md`.

**Tech Stack:** GitHub Actions YAML, Gradle, Android release build, Java 21

---

## File map

- Create: `.github/workflows/manual-release-artifact.yml`
  - New manual workflow that decodes the keystore, builds `assembleRelease`, and uploads `app-release.apk` as an artifact.
- Modify: `README.md`
  - Add short instructions for manually generating and downloading the full APK artifact from GitHub Actions.
- Reference: `.github/workflows/release.yml`
  - Existing release workflow used as the source of truth for signing-related steps and output paths.

### Task 1: Add the manual release artifact workflow

**Files:**
- Create: `.github/workflows/manual-release-artifact.yml`
- Reference: `.github/workflows/release.yml`

- [ ] **Step 1: Write the failing validation command**

```bash
python3 - <<'PY'
from pathlib import Path

workflow = Path("/workspace/.github/workflows/manual-release-artifact.yml")
assert workflow.exists(), "workflow file is missing"
text = workflow.read_text()

required_fragments = [
    "name: Manual Release Artifact",
    "workflow_dispatch:",
    "java-version: 21",
    "KEYSTORE_BASE64",
    "SIGNING_PASSWORD",
    "./gradlew assembleRelease",
    "actions/upload-artifact",
    "app/build/outputs/apk/release/app-release.apk",
]

for fragment in required_fragments:
    assert fragment in text, f"missing fragment: {fragment}"
PY
```

- [ ] **Step 2: Run validation to verify it fails**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

workflow = Path("/workspace/.github/workflows/manual-release-artifact.yml")
assert workflow.exists(), "workflow file is missing"
text = workflow.read_text()

required_fragments = [
    "name: Manual Release Artifact",
    "workflow_dispatch:",
    "java-version: 21",
    "KEYSTORE_BASE64",
    "SIGNING_PASSWORD",
    "./gradlew assembleRelease",
    "actions/upload-artifact",
    "app/build/outputs/apk/release/app-release.apk",
]

for fragment in required_fragments:
    assert fragment in text, f"missing fragment: {fragment}"
PY
```

Expected: FAIL with `AssertionError: workflow file is missing`

- [ ] **Step 3: Write the minimal workflow**

Create `.github/workflows/manual-release-artifact.yml` with:

```yaml
name: Manual Release Artifact

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 21

      - uses: gradle/actions/setup-gradle@v4

      - name: Decode keystore
        env:
          KEYSTORE_BASE64: ${{ secrets.KEYSTORE_BASE64 }}
        run: echo "$KEYSTORE_BASE64" | base64 -d > app/scrib-upload.jks

      - name: Build release APK
        run: ./gradlew assembleRelease
        env:
          SIGNING_PASSWORD: ${{ secrets.SIGNING_PASSWORD }}

      - name: Upload release APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: scrib-release-apk
          path: app/build/outputs/apk/release/app-release.apk
          if-no-files-found: error
```

- [ ] **Step 4: Run validation to verify it passes**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

workflow = Path("/workspace/.github/workflows/manual-release-artifact.yml")
assert workflow.exists(), "workflow file is missing"
text = workflow.read_text()

required_fragments = [
    "name: Manual Release Artifact",
    "workflow_dispatch:",
    "java-version: 21",
    "KEYSTORE_BASE64",
    "SIGNING_PASSWORD",
    "./gradlew assembleRelease",
    "actions/upload-artifact",
    "app/build/outputs/apk/release/app-release.apk",
]

for fragment in required_fragments:
    assert fragment in text, f"missing fragment: {fragment}"
print("workflow validation passed")
PY
```

Expected: PASS with `workflow validation passed`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/manual-release-artifact.yml
git commit -m "ci: add manual release artifact workflow"
```

### Task 2: Document how to download the full APK

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write the failing documentation validation command**

```bash
python3 - <<'PY'
from pathlib import Path

readme = Path("/workspace/README.md").read_text()
required_lines = [
    "## Download full APK",
    "GitHub Actions",
    "Manual Release Artifact",
    "scrib-release-apk",
]

for line in required_lines:
    assert line in readme, f"missing README text: {line}"
PY
```

- [ ] **Step 2: Run validation to verify it fails**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

readme = Path("/workspace/README.md").read_text()
required_lines = [
    "## Download full APK",
    "GitHub Actions",
    "Manual Release Artifact",
    "scrib-release-apk",
]

for line in required_lines:
    assert line in readme, f"missing README text: {line}"
PY
```

Expected: FAIL with `missing README text: ## Download full APK`

- [ ] **Step 3: Add the minimal README section**

Append this section to `README.md` after `## Build`:

```md
## Download full APK

To build a full installable APK from GitHub:

1. Open the repository `Actions` tab.
2. Select the `Manual Release Artifact` workflow.
3. Click `Run workflow`.
4. Wait for the job to finish.
5. Download the `scrib-release-apk` artifact from the run page.

This workflow builds the signed release APK using the repository signing secrets.
```

- [ ] **Step 4: Run validation to verify it passes**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

readme = Path("/workspace/README.md").read_text()
required_lines = [
    "## Download full APK",
    "GitHub Actions",
    "Manual Release Artifact",
    "scrib-release-apk",
]

for line in required_lines:
    assert line in readme, f"missing README text: {line}"
print("README validation passed")
PY
```

Expected: PASS with `README validation passed`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: document manual APK artifact flow"
```

### Task 3: Verify the workflow on GitHub

**Files:**
- Reference: `.github/workflows/manual-release-artifact.yml`
- Reference: `README.md`

- [ ] **Step 1: Push the implementation branch**

Run:

```bash
git push
```

Expected: branch updates successfully on `origin`

- [ ] **Step 2: Open or update the pull request**

Action:

- Open the repository on GitHub
- Create or update a pull request for the workflow change

Expected: an open PR exists for the workflow change and shows the new workflow file plus the `README.md` update

- [ ] **Step 3: Merge after review**

Action:

- Merge the pull request into `main` after review

Expected: changes land on `main`

- [ ] **Step 4: Run the workflow manually on GitHub**

Action:

- Open the repository `Actions` tab
- Select `Manual Release Artifact`
- Click `Run workflow`

Expected: GitHub accepts the manual dispatch and starts a new workflow run

- [ ] **Step 5: Verify artifact availability**

Action:

- Open the latest `Manual Release Artifact` run
- Confirm the run succeeds
- Confirm the run contains the `scrib-release-apk` artifact
- Download the artifact and verify it contains the release APK

Expected: the artifact is present and downloadable from the run page

- [ ] **Step 6: Commit**

```bash
git status
```

Expected: no local changes; no additional commit required for this verification task

## Self-review

- Spec coverage: the plan adds a manual workflow, reuses existing signing secrets, uploads a full release APK artifact, preserves the existing tag-based release flow, and documents how to use the new flow.
- Placeholder scan: no `TODO`, `TBD`, or implied implementation gaps remain.
- Type consistency: the workflow name, artifact name, secrets, and APK path are used consistently across tasks.
