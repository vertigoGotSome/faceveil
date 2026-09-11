# Review and release workflow

The current working branch is `1-feat-add-virtual-camera-output`. Changes in this
work session were not committed or pushed. Review the diff locally before committing.

1. Keep issue #1 as the feature's acceptance checklist. Record device installation,
   an actual receiving application's test, and shutdown/privacy tests separately.
2. Commit coherent pieces with names such as `feat: isolate virtual camera output`,
   `fix: latch privacy shield`, and `docs: explain virtual camera setup`.
3. Open a pull request into `main`, link issue #1, describe visible behavior and
   remaining limitations, and attach a screenshot containing no personal camera feed.
4. Wait for the **Quality / quality** workflow job. Review locally as well; automated
   tests do not establish compatibility with every webcam, driver or receiving app.
5. Merge only after testing the real device. Use `Closes #1` only when all acceptance
   criteria are met. Prepare the version and release notes together; the existing
   package metadata (0.1.0), UI (0.2), and tag (0.2.0) need reconciliation before release.

## Suggested repository settings

Protect `main`: require pull requests and the successful quality check, disable force
pushes and branch deletion. Require another review when a collaborator is available;
a solo maintainer cannot approve their own pull request. Consider squash merging and
automatic deletion of merged feature branches. Branch protection is available for
public repositories on GitHub Free; private-repository availability depends on plan.
See [GitHub's branch-protection documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

The connected repository was **public** at inspection on 2026-09-11. Earlier project
notes calling it private are historical. No visibility or other remote setting was
changed during this work.

## Licensing decision before distribution

No project license has been selected. Public visibility alone does not grant an
open-source license. Decide the intended permissions before accepting contributions
or shipping downloads. `pyvirtualcam` declares GPL-2.0; Unity Capture's filter is MIT.
Check the exact dependency terms and distribution obligations before selecting a
project license. Do not assume an MIT project license makes bundled GPL code permissive.
Keep third-party notices, model licenses and corresponding source obligations in the
release process. Upstream: [pyvirtualcam](https://github.com/letmaik/pyvirtualcam),
[Unity Capture](https://github.com/schellingb/UnityCapture).

An easy-download release still needs packaging, a clean-machine installation test,
and a decision about signing and distributing the Windows camera component. The
development environment and installer in this branch are not a tested consumer installer.
