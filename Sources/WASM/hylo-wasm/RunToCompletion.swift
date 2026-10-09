@_spi(ExperimentalCustomExecutors) import _Concurrency

/// Returns the result of `work`, running Swift's executor on the calling thread until there is one.
///
/// A reactor's exports are called by its host and must return synchronously, and a reactor has no
/// `async` entry point whose return would drain the executor, so a task started from an export
/// would otherwise never run. On WASI the main executor is a cooperative run loop that also runs
/// the tasks of the default executor, so running it until `work` has finished runs every task
/// `work` waits for.
func runToCompletion<T>(_ work: @escaping @Sendable () async -> T) -> T {
  let outcome = Outcome<T>()
  Task { outcome.value = await work() }
  do {
    try MainActor.executor.runUntil { outcome.value != nil }
  } catch {
    fatalError("the executor stopped: \(error)")
  }
  return outcome.value!
}

/// The result of a task, written by the task and read once the executor has run it.
///
/// `@unchecked Sendable` because the task writes it and the thread running the executor reads it,
/// which are one and the same thread on WASI.
private final class Outcome<T>: @unchecked Sendable {

  /// The result, once the task has finished.
  var value: T?

}
