SQL + DSA LAB - PORTABLE EDITION

WINDOWS 10 / 11 (64-bit Intel or AMD)
1. Extract the ENTIRE ZIP into a normal folder.
2. Open start.exe (Windows may show the name as start).
3. Your browser opens in DSA mode. Switch between DBMS / DSA in the header.

Python and a C compiler are included. No installation, internet connection,
account, Oracle, Node.js, or pip packages are needed. Keep the console open.
Press Ctrl+C or close it to stop. Do not run from inside the ZIP.
start.cmd is an alternative Windows launcher.

If another app occupies port 8765, run: start.exe --port 8766
If the browser does not open, visit http://127.0.0.1:8766/?mode=dsa
(Use 8765 if you did not change the port.)

MACOS / LINUX
The included runtime and compiler are Windows-only. The app source is portable.
Install Python 3.10+ and GCC or Clang, then run: sh start.sh
On macOS, start.command is also provided; grant execute permission if needed.

CONTENT AND PROGRESS
107 DBMS exercises in 12 rounds. 40 DSA exercises in 5 rounds.
Drafts and progress live in this browser, separately for DBMS and DSA.
Keep the same browser and port to retain them. Progress does not travel with
this ZIP. Review provides a JSON export.

The SQL/PLSQL runner is a teaching subset, not a complete Oracle database.
C code runs locally with a time limit, not in a security sandbox.
Use your own practice code. The website binds only to 127.0.0.1.

UPDATES, SOURCE AND ISSUES
https://github.com/gaurvknsl/sql-lab
https://github.com/gaurvknsl/sql-lab/releases/latest
Download a fresh release to update; keep using the same browser and port.

THIRD-PARTY SOFTWARE
Python: runtime/LICENSE.txt, including bundled-library notices.
TinyCC 0.9.27: compiler/COPYING and included notices.
Unmodified corresponding source: third-party/tcc-0.9.27-source.tar.bz2
Official sources: https://www.python.org/ and https://bellard.org/tcc/
The native Windows launcher source is start-source.c.
The complete website source and tests are under app/.
