#! /bin/bash
#
# pyinstaller --noconfirm --log-level=WARN \
#     --onefile --nowindow \
#     --hidden-import=secret1 \
#     --hidden-import=secret2 \
#     --upx-dir=/usr/local/share/ \
#     myscript.spec
PYTHONPATH=$(pwd)/src pyinstaller \
  --verbose \
  --log-level=WARN \
  --distpath src/exe-dist \
  --workpath src/exe-build \
  src/exe-spec/authenticator.spec
