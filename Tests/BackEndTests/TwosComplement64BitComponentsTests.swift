@testable import BackEnd
import BigInt
import XCTest

final class TwosComplement64BitComponentsTests: XCTestCase {

  func testNonNegative() {
    XCTAssertEqual(BigInt(42).twosComplement64BitComponents(bitWidth: 32), [42])
    XCTAssertEqual(BigInt(42).twosComplement64BitComponents(bitWidth: 128), [42, 0])
    let m = (BigInt(1) << 127) - 1
    XCTAssertEqual(m.twosComplement64BitComponents(bitWidth: 128), [.max, .max >> 1])
  }

  func testNegative() {
    XCTAssertEqual(BigInt(-1).twosComplement64BitComponents(bitWidth: 32), [.max])
    XCTAssertEqual(BigInt(-1).twosComplement64BitComponents(bitWidth: 64), [.max])
    XCTAssertEqual(BigInt(-1).twosComplement64BitComponents(bitWidth: 128), [.max, .max])
    XCTAssertEqual(BigInt(-2).twosComplement64BitComponents(bitWidth: 128), [.max - 1, .max])

    let n = -(BigInt(1) << 64) - 1
    XCTAssertEqual(n.twosComplement64BitComponents(bitWidth: 128), [.max, .max - 1])
    let m = -(BigInt(1) << 127)
    XCTAssertEqual(m.twosComplement64BitComponents(bitWidth: 128), [0, 1 << 63])
  }

}
