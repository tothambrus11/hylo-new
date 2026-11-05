#if canImport(Glibc)
import Glibc
#elseif canImport(Darwin)
import Darwin
#elseif canImport(WASILibc)
import WASILibc
#endif

/// Research instrumentation: event counters for the type checker.
///
/// Not thread-safe; only meaningful when a single module is typed at a time.
public enum TyperCounters {

  /// The values of the counters, indexed by name.
  nonisolated(unsafe) public static var values: [String: Int] = [:]

  /// `true` iff counting is enabled.
  nonisolated(unsafe) public static var enabled = false

  /// Increments the counter `k` by `n`.
  @inline(__always)
  public static func bump(_ k: StaticString, by n: Int = 1) {
    if enabled { values["\(k)", default: 0] += n }
  }

  /// Resets all counters.
  public static func reset() { values = [:] }

  /// Returns a textual snapshot of the counters.
  public static func snapshot() -> String {
    values.sorted(by: { $0.key < $1.key }).map({ "\($0.key)=\($0.value)" }).joined(separator: " ")
  }

}

/// Research flags enabling experimental optimizations, read from `HYLO_TC_EXPERIMENTS`
/// (a comma-separated list, e.g. `names,unify,index,absmodel`).
public enum TyperExperiments {

  /// The set of enabled experiments.
  nonisolated(unsafe) public static var enabled: Set<String> = {
    guard let p = getenv("HYLO_TC_EXPERIMENTS") else { return [] }
    return Set(String(cString: p).split(separator: ",").map(String.init))
  }()

  /// Name-filter extensions before checking whether they apply to a type.
  nonisolated(unsafe) public static var names: Bool = enabled.contains("names")

  /// Dispatch unification on type tags before casting.
  nonisolated(unsafe) public static var unify: Bool = enabled.contains("unify")

  /// Index givens by the head constructor of their conclusion.
  nonisolated(unsafe) public static var index: Bool = enabled.contains("index")

  /// Defer overload branching and prune choices by forward checking.
  nonisolated(unsafe) public static var solver: Bool = enabled.contains("solver")

  /// Prune resolution subgoals identical to one of their ancestors.
  nonisolated(unsafe) public static var loopcheck: Bool = enabled.contains("loopcheck")

  /// Refute queries using an abstract least model of the givens.
  nonisolated(unsafe) public static var absmodel: Bool = enabled.contains("absmodel")

  /// The truncation depth of the abstract model.
  nonisolated(unsafe) public static var absDepth: Int = {
    guard let p = getenv("HYLO_TC_ABSDEPTH") else { return 3 }
    return Int(String(cString: p)) ?? 3
  }()

}

/// A monotonic clock for research instrumentation.
public enum TyperClock {

  /// Returns the current time in milliseconds.
  public static func now() -> Double {
    var t = timespec()
    clock_gettime(CLOCK_MONOTONIC, &t)
    return Double(t.tv_sec) * 1e3 + Double(t.tv_nsec) / 1e6
  }

}
