#include "WasmLinker.h"

#include "lld/Common/Driver.h"
#include "llvm/Support/raw_ostream.h"

#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

LLD_HAS_DRIVER(wasm)

extern "C" int hylo_wasm_link(int argc, const char *const *argv, char **diagnostics) {
  std::vector<const char *> arguments(argv, argv + argc);
  std::string output;
  llvm::raw_string_ostream stream(output);

  lld::Result r = lld::lldMain(arguments, stream, stream, {{lld::Wasm, &lld::wasm::link}});
  stream.flush();

  *diagnostics = strdup(output.c_str());
  return r.retCode;
}
