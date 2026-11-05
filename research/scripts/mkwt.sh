#!/bin/bash
# Usage: mkwt.sh NAME [PATCH]  — create /home/hylo/hylo-tc/wt/NAME: a detached worktree of hylo-new at HEAD
# with PATCH (default: the current uncommitted diff of hylo-new) applied and Swifty-LLVM checked out.
set -euo pipefail
NAME=$1; MAIN=/home/hylo/hylo-tc/hylo-new; WT=/home/hylo/hylo-tc/wt/$NAME
PATCH=${2:-}
cd $MAIN
if [ -z "$PATCH" ]; then PATCH=/home/hylo/hylo-tc/wt/$NAME.base.patch; git diff --binary > $PATCH; fi
[ -d $WT ] && { echo "exists: $WT"; exit 0; }
git worktree add --detach $WT HEAD >/dev/null
cd $WT
git apply --whitespace=nowarn $PATCH
git -c protocol.file.allow=always submodule update --init --reference $MAIN/Swifty-LLVM >/dev/null 2>&1 || \
  git -c protocol.file.allow=always submodule update --init --reference ~/hylo-new/Swifty-LLVM
echo $WT
