#!/bin/bash
# Fetches the comparable code bases counted by census.py: shallow, blob-less, sparse clones into ./clones.
# The census of this directory was made at the commits listed below (all clones succeeded on 2026-11-10).
#   hylo-lang/hylo           6889158246df571baa9079115817ab2bff61156b   StandardLibrary
#   swiftlang/swift          a8a3df65454a72a5c158884839509d07cef12283   stdlib/public/core
#   apple/swift-collections  d01e52d04d20b8f6e83a16acfb15db3eaab6743c   Sources
#   apple/swift-algorithms   5b7143f8e291dee0e14c118fd0212487f0b37af5   Sources
#   rust-lang/rust           ac8310ba643a3796cbe77d2e06944d7c8513999f   library/core/src/{iter,ops,slice}, library/alloc/src/{collections,vec}
# The clones are data: census.py only reads them as text.
set -e
mkdir -p "$(dirname "$0")/clones" && cd "$(dirname "$0")/clones"
get() { # owner/repo directory paths...
  local repo=$1 dir=$2; shift 2
  [ -d "$dir" ] || git clone --depth 1 --filter=blob:none --sparse "https://github.com/$repo" "$dir"
  git -C "$dir" sparse-checkout set "$@"
}
get hylo-lang/hylo hylo StandardLibrary
get swiftlang/swift swift stdlib/public/core
get apple/swift-collections swift-collections Sources
get apple/swift-algorithms swift-algorithms Sources
get rust-lang/rust rust library/core/src/iter library/core/src/ops library/core/src/slice library/alloc/src/collections library/alloc/src/vec
