@testable import BackEnd
import BigInt
import XCTest

final class TwosComplementWordsTests: XCTestCase {

  func testNonNegative() {
    XCTAssertEqual(BigInt(42).twosComplementWords(bitWidth: 32), [42])
    XCTAssertEqual(BigInt(42).twosComplementWords(bitWidth: 128), [42, 0])
    let m = (BigInt(1) << 127) - 1
    XCTAssertEqual(m.twosComplementWords(bitWidth: 128), [.max, .max >> 1])
  }

  func testNegative() {
    XCTAssertEqual(BigInt(-1).twosComplementWords(bitWidth: 32), [.max])
    XCTAssertEqual(BigInt(-1).twosComplementWords(bitWidth: 64), [.max])
    XCTAssertEqual(BigInt(-1).twosComplementWords(bitWidth: 128), [.max, .max])
    XCTAssertEqual(BigInt(-2).twosComplementWords(bitWidth: 128), [.max - 1, .max])

    let n = -(BigInt(1) << 64) - 1
    XCTAssertEqual(n.twosComplementWords(bitWidth: 128), [.max, .max - 1])
    let m = -(BigInt(1) << 127)
    XCTAssertEqual(m.twosComplementWords(bitWidth: 128), [0, 1 << 63])
  }

}
