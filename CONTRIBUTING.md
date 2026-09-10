# Contributing to FaceVeil

FaceVeil is currently developed as a private solo project, but it deliberately uses a professional Git/GitHub workflow.

The goal is to keep changes traceable, testable, and reviewable without introducing unnecessary process overhead.

## Development workflow

The preferred workflow is:

```text
Idea
  ↓
GitHub Issue
  ↓
Feature Branch
  ↓
Implementation
  ↓
Tests + Ruff
  ↓
Commit
  ↓
Pull Request
  ↓
CI / Review
  ↓
Merge to main
```

## Issues

Non-trivial work should normally start with a GitHub Issue.

An issue should describe:

- the goal
- why the change is useful
- scope
- acceptance criteria
- relevant limitations
- explicitly out-of-scope work where useful

Do not use an issue as a detailed implementation transcript.

The issue defines the desired result; implementation details can evolve during development.

## Labels

FaceVeil currently uses three main label dimensions.

### Type

- `type: feature`
- `type: bug`
- `type: maintenance`

### Area

Examples:

- `area: capture`
- `area: detection`
- `area: ui`
- `area: virtual-camera`

Additional area labels may be added when the architecture grows.

### Priority

- `priority: high`
- `priority: normal`
- `priority: low`

Priority represents project importance, not development difficulty.

## Milestones

Milestones are used for larger product goals.

Example:

```text
v0.2.0 — Virtual Camera Output
```

Issues should be assigned to a milestone when they directly contribute to that release goal.

## Branches

Feature branches should normally be associated with an issue.

GitHub-generated issue branches may use names such as:

```text
1-feat-add-virtual-camera-output
```

Manually created branches may use a concise convention such as:

```text
feat/12-camera-discovery
fix/15-preview-timeout
docs/18-architecture-update
```

Do not create a second branch for the same issue unless there is a concrete reason.

Always verify the current branch before starting work:

```powershell
git branch --show-current
```

## Commits

Use small, logically scoped commits.

Preferred format:

```text
<type>(<scope>): <short English description>
```

Examples:

```text
feat(output): add virtual camera backend abstraction
feat(ui): add virtual camera controls
fix(capture): handle disconnected cameras
test(output): cover virtual camera lifecycle
docs: update virtual camera setup
refactor(pipeline): simplify privacy target selection
chore(deps): update development dependencies
```

Common commit types:

- `feat`
- `fix`
- `test`
- `docs`
- `refactor`
- `chore`

Avoid large commits containing unrelated changes.

## Before editing

Before making substantial changes:

```powershell
git status
git branch --show-current
git log --oneline --decorate -n 10
```

When resuming work after a longer break, also inspect the relevant source files before modifying them.

The repository contents are the source of truth.

## Before committing

Always inspect the current state:

```powershell
git status
git diff
```

Then run:

```powershell
python -m ruff check .
python -m pytest -v
```

Do not commit:

- `.venv`
- credentials
- API keys
- personal recordings
- camera captures
- temporary debug files
- generated shell artifacts
- unrelated editor files

## Testing philosophy

Tests should verify intended application behavior.

Do not change correct production architecture merely to satisfy an outdated test.

If a refactor intentionally changes a contract:

1. verify that the new architecture is correct
2. update the tests to reflect the new contract
3. preserve equivalent behavioral coverage

Do not silently weaken tests just to make CI green.

## Hardware-related changes

Changes involving:

- camera capture
- camera enumeration
- virtual-camera output
- GPU/OpenGL behavior

may require manual hardware testing in addition to automated tests.

Document relevant manual testing in the Pull Request.

For capture-related changes, consider testing:

- start
- stop
- restart
- missing camera
- disconnected camera
- device refresh
- camera switching
- video-file input
- video EOF
- input-source switching

For virtual-camera changes, consider testing:

- backend unavailable
- output start
- output stop
- repeated start/stop
- capture continues independently
- Discord/OBS/browser visibility
- correct frame dimensions
- expected FPS behavior

## Privacy-related changes

FaceVeil must not make unverified anonymity guarantees.

Language in code, documentation, and UI should distinguish between:

- privacy-oriented visual filtering
- detector confidence
- actual anonymity guarantees

Face detection can fail.

Pixelation and blur are visual effects, not cryptographic or certified anonymization.

## Architecture principles

Prefer clear module boundaries.

Current responsibilities include:

```text
app.py
    UI and lifecycle

capture.py
    capture worker

devices.py
    camera discovery

detector.py
    face detection

pipeline.py
    privacy logic

filters.py
    image effects

preview.py
    local rendering

transport.py
    shared frame transport

virtual_camera.py
    virtual-camera output abstraction
```

Avoid duplicating:

- capture loops
- face detection
- privacy processing

A processed frame should be reusable by both preview and output backends.

## Pull Requests

Pull Requests should normally target:

```text
main
```

A PR should include:

- what changed
- why it changed
- associated issue
- important architecture decisions
- test results
- manual hardware test results where relevant
- known limitations

Use:

```text
Closes #<issue>
```

only when the PR genuinely completes the issue.

For partial implementations or proofs of concept, reference the issue without automatically closing it.

## Definition of Done

A change is complete when applicable items are satisfied:

- acceptance criteria are met
- relevant error cases are handled
- Ruff passes
- automated tests pass
- manual hardware tests are documented where needed
- documentation reflects changed behavior
- no known regression is introduced
- privacy claims remain accurate
- the Pull Request diff is understood and reviewable

## Main branch

`main` should remain functional.

Experimental or incomplete larger features should remain on feature branches until they are ready.

Branch protection may later require:

- Pull Requests before merge
- successful CI
- prevention of force pushes
- prevention of branch deletion
