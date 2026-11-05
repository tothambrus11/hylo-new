import Foundation
import FrontEnd
import StandardLibrary

/// Research harness: times the front-end phases on the standard library and on user files.
///
/// Usage: tc-bench [--repeat N] [--quiet] [--per-file] file.hylo ...
@main
struct TypeCheckBench {

  static func now() -> Double {
    var t = timespec()
    clock_gettime(CLOCK_MONOTONIC, &t)
    return Double(t.tv_sec) * 1e3 + Double(t.tv_nsec) / 1e6
  }

  static func main() async throws {
    var args = Array(CommandLine.arguments.dropFirst())
    var repeats = 1
    var quiet = false
    if let i = args.firstIndex(of: "--repeat") {
      repeats = Int(args[i + 1])!
      args.removeSubrange(i ... i + 1)
    }
    if let i = args.firstIndex(of: "--quiet") {
      quiet = true
      args.remove(at: i)
    }
    var dumpPath: String? = nil
    if let i = args.firstIndex(of: "--dump") {
      dumpPath = args[i + 1]
      args.removeSubrange(i ... i + 1)
    }
    if let i = args.firstIndex(of: "--count") {
      TyperCounters.enabled = true
      args.remove(at: i)
    }

    var best: [String: Double] = [:]
    for _ in 0 ..< repeats {
      TyperCounters.reset()
      var p = Program(forTesting: true)
      var phases: [(String, Double)] = []
      var t0 = now()

      let s = p.demandModule(Module.standardLibraryName)
      try SourceFile.forEach(in: bundledStandardLibrarySources) { (f) in
        _ = p[s].addSource(f)
      }
      let m = p.demandModule(.init("Test"))
      p[m].addDependency(Module.standardLibraryName)
      for a in args {
        let f = try SourceFile(contentsOf: URL(fileURLWithPath: a))
        _ = p[m].addSource(f)
      }
      phases.append(("parse", now() - t0)); t0 = now()

      for m in p.moduleIdentities { await p.assignScopes(m) }
      phases.append(("scope", now() - t0)); t0 = now()

      if getenv("TC_NO_STD") == nil { p.assignTypes(s, loggingInferenceWhere: nil) }
      phases.append(("type.stdlib", now() - t0)); t0 = now()
      let stdlibCounters = TyperCounters.snapshot()
      TyperCounters.reset()

      p.assignTypes(m, loggingInferenceWhere: nil)
      phases.append(("type.user", now() - t0)); t0 = now()
      let userCounters = TyperCounters.snapshot()

      if let path = dumpPath {
        var out = ""
        for x in [s, m] {
          out += "== module \(p[x].name)\n"
          for l in p.semanticDump(of: x) { out += l; out += "\n" }
        }
        for d in Array(p.diagnostics).map({ "\($0)" }).sorted() { out += "diag \(d)\n" }
        try out.write(toFile: path, atomically: true, encoding: .utf8)
      }
      for (k, v) in phases { best[k] = min(best[k] ?? .infinity, v) }
      best["_stdlibCounters"] = 0
      if !quiet {
        print("counters.stdlib:", stdlibCounters)
        print("counters.user:  ", userCounters)
        let ds = Array(p.diagnostics)
        print("diagnostics:", ds.count)
        for d in ds.map({ "\($0)" }).sorted() { print("  ", d) }
      }
    }
    for k in ["parse", "scope", "type.stdlib", "type.user"] {
      print(String(format: "%-12@ %9.2f ms", k as NSString, best[k]!))
    }
  }

}
