# Repository maintenance

This is the user's SQL + DSA practice website. The canonical public repository is
https://github.com/gaurvknsl/sql-lab, on branch `main`.

The user explicitly requested that future website changes made in this chat also
be published to this repository. After completing an authorized change, update
the README and relevant documentation, run appropriate tests, commit the change,
and push it. Do not force-push, publish unrelated local work, or expose secrets,
browser progress, source syllabus attachments, or device-specific file paths.
Report any authentication, push, or CI failure honestly.

Preserve the DBMS and DSA modes, their separate local storage keys, and the
loopback-only server. C programs run locally; do not describe this as a security
sandbox. Maintain the portable Windows release and its compiler/runtime license
notices when changing packaging. macOS/Linux source launchers require installed
Python and a C compiler.

The `portable.yml` workflow builds a fresh portable archive on pushes to `main`
and publishes it as a release asset on `v*` tags. Do not create recurring scheduled
tasks for this repository: the user chose updates when we change the website here.
