import Foundation

extension FileManager {

  /// Calls `action` with the URL of a file containing `s`.
  public func withTemporaryFile<T>(containing s: String, _ action: (URL) throws -> T) throws -> T {
    let u = temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: false)
    try s.write(to: u, atomically: true, encoding: .utf8)
    return try action(u)
  }

  /// The URL to the working directory for the current process.
  public var currentDirectoryURL: URL {
    .init(fileURLWithPath: FileManager.default.currentDirectoryPath, isDirectory: true)
  }

  /// Creates an empty temporary directory for the duration of the given observer.
  public func withUniqueTemporaryDirectory<T>(_ observer: (URL) throws -> T) throws -> T {
    let directory = temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
    try createDirectory(at: directory, withIntermediateDirectories: true)
    defer { try? removeItem(at: directory) }
    return try observer(directory)
  }  
  
  /// Creates an empty temporary directory for the duration of the given observer.
  public func withUniqueTemporaryDirectory<T>(_ observer: (URL) async throws -> T) async throws -> T {
    let directory = temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
    try createDirectory(at: directory, withIntermediateDirectories: true)
    defer { try? removeItem(at: directory) }
    return try await observer(directory)
  }

}
