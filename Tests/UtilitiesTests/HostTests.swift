import Foundation
import Utilities
import XCTest
typealias Host = Utilities.Host

final class HostTests: XCTestCase {

  func testFindNativeExecutableThrowsForUnknownCommand() throws {
    try XCTAssertThrowsError(try Host.findNativeExecutable(invokedAs: "randomNotFoundExecutable")) { error in
      let e = try XCTUnwrap(error as? Host.ExecutableNotFound)
      XCTAssertEqual(e.name, "randomNotFoundExecutable")
      XCTAssertEqual(e.description, "Executable not found on PATH: randomNotFoundExecutable")
    }
  }

  #if os(Windows)
    func testFindNativeExecutableFindsAndExecutesWhereExe() throws {
      let whereExe = try Host.findNativeExecutable(invokedAs: "where")
      XCTAssertEqual(whereExe.lastPathComponent.lowercased(), "where.exe")

      let output = try Process.executionOutput(whereExe, arguments: ["cmd"])
      XCTAssertTrue(output.lowercased().contains("cmd.exe"))
    }
  #else
    func testFindNativeExecutableFindsAndExecutesBash() throws {
      let bash = try Host.findNativeExecutable(invokedAs: "bash")
      XCTAssertEqual(bash.lastPathComponent, "bash")

      let output = try Process.executionOutput(bash, arguments: ["-lc", "printf '%s' bash-ok"])
      XCTAssertEqual(output, "bash-ok")
    }
  #endif

  func testExecutionOutputThrowsOnNonzeroExit() throws {
    #if os(Windows)
      let executable = try Host.findNativeExecutable(invokedAs: "cmd")
      let arguments = ["/c", "exit", "42"]
    #else
      let executable = try Host.findNativeExecutable(invokedAs: "bash")
      let arguments = ["-lc", "exit 42"]
    #endif

    try XCTAssertThrowsError(Process.executionOutput(executable, arguments: arguments)) { error in
      let e = try XCTUnwrap(error as? Process.NonzeroExit)
      XCTAssertEqual(e.exitCode, 42)
      XCTAssertEqual(e.executable, executable)
      XCTAssertEqual(e.arguments, arguments)
    }
  }

}
