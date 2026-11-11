import XCTest

@testable import FrontEnd

/// Tests that demangling recovers the structure of mangled symbols.
///
/// Getting the end of a declaration chain wrong typically produces symbols that demangle without
/// any error but into the wrong structure. Hence, these tests compare demangled symbols with the
/// program from which they have been mangled rather than checking for the absence of `#!`.
final class ManglingStructureRecoveryTests: XCTestCase {

  /// Tests that each declaration of `program` extended with `syntheticFunctionsCode` demangles to
  /// a qualified name whose components describe that declaration and the scopes containing it.
  func testDeclarationNames() async {
    let (p, m0) = await typeCheckedWithMinimalStandardLibrary(
      .init(contents: program + syntheticFunctionsCode))
    for n in p.select(from: m0, .satisfies({ (n) in p.isDeclaration(n) })) {
      let d = DeclarationIdentity(uncheckedFrom: n)
      let m = p.mangled(d)
      guard let e = entity(m) else { continue }
      XCTAssert(
        qualifiedName(e, describes: d, relativeTo: nil, in: p),
        "demangling of \(p.debugName(of: d)) has the wrong structure: \(e)\n(mangled: \(m))")
    }
  }

  /// Tests that IR function names demangle to the entities they denote, for every kind of name
  /// that does not contain another name.
  func testFunctionNames() async {
    var (p, m0) = await typeCheckedWithMinimalStandardLibrary(.init(contents: program))
    let bases = baseNames(in: m0, of: &p)

    // Together with the names that contain another name, `bases` covers every kind of name.
    let wrapped = wrappers(tags: [0]).map({ (w) in w.name(bases[0].name) })
    XCTAssertEqual(
      Set((bases.map(\.name) + wrapped).map(\.kind)), Set(IRFunction.Name.Kind.allCases))

    for b in bases {
      let m = p.mangled(b.name)
      guard let e = entity(m) else { continue }
      XCTAssert(
        b.isExpectedDemangling(e),
        "demangling of \(b.name) has the wrong structure: \(e)\n(mangled: \(m))")
    }
  }

  /// Tests that each kind of IR function name containing another name `n` demangles to the
  /// corresponding entity containing the demangling of `n`, with a range of tags.
  ///
  /// The demangling of `n` itself is checked by `testFunctionNames`.
  func testWrappedFunctionNames() async {
    var (p, m0) = await typeCheckedWithMinimalStandardLibrary(.init(contents: program))

    // Small tags, including all those encoded with a single character (some of which read as
    // entity operators), tags at the boundaries of the variable-length integer encoding, and a
    // large one.
    let tags = Array(0 ..< 64) + [114, 115, 4209, 4210, 1 << 20]

    for b in baseNames(in: m0, of: &p) {
      guard let e = entity(p.mangled(b.name)) else { continue }
      for w in wrappers(tags: tags) {
        assertDemangling(of: w.name(b.name), is: w.entity(e), in: p)
      }
    }
  }

  /// Tests that each kind of IR function name containing another name, itself containing a name
  /// `n`, demangles to the corresponding entity containing the demangling of `n`.
  ///
  /// The demangling of `n` itself is checked by `testFunctionNames`.
  func testNestedWrappedFunctionNames() async {
    var (p, m0) = await typeCheckedWithMinimalStandardLibrary(.init(contents: program))

    // A few of the tags used by `testWrappedFunctionNames`.
    let tags = [0, 9, 10, 36, 46, 51, 115]

    for b in baseNames(in: m0, of: &p) {
      guard let e = entity(p.mangled(b.name)) else { continue }
      for v in wrappers(tags: tags) {
        // The two wrappers use different tags so that they are distinguishable.
        for w in wrappers(tags: tags) where (v.tag == nil) || (v.tag != w.tag) {
          assertDemangling(of: w.name(v.name(b.name)), is: w.entity(v.entity(e)), in: p)
        }
      }
    }
  }

  /// Tests that the number of inputs of an arrow is not read as the continuation of the
  /// declaration chain that ends the environment of that arrow.
  func testItemCountAfterDeclarationChain() async {
    var (p, m0) = await typeCheckedWithMinimalStandardLibrary(.init(contents: program))
    let a = p.firstDeclaration(StructDeclaration.self, named: "A", in: m0)!
    let t = p.types.demand(Struct(declaration: a)).erased
    guard let x = type(p.mangled(t)) else { return }

    // 10 is the smallest number encoded with a letter (i.e., "a"). The label of the first input
    // has 39 characters so that its mangled length (i.e., "F") reads as an operator continuing a
    // declaration chain when it comes right after "a" (i.e., "aF").
    let labels = [String(repeating: "x", count: 39)] + (1 ..< 10).map({ (i) in "l\(i)" })
    let arrow = p.types.demand(
      Arrow(
        environment: t,
        inputs: labels.map({ (l) in .init(label: l, access: .let, type: t) }),
        output: t))
    let expected = DemangledType.arrow(
      style: .parenthesized, effect: .let, environment: x,
      inputs: labels.map({ (l) in .init(label: l, type: x) }), output: x)

    let m = p.mangled(arrow)
    XCTAssertEqual(
      type(m), expected, "demangling of an arrow with 10 inputs is incorrect\n(mangled: \(m))")
  }

  /// Tests that symbols are looked up at the right position when they come after a declaration
  /// that occurs in its own qualification.
  func testLookupAfterDeclarationOccurringInItsQualification() async {
    var (p, m0) = await typeCheckedWithMinimalStandardLibrary(
      .init(contents: program + "fun generic<T>(x: T) {}\n"))
    let f = p.firstDeclaration(FunctionDeclaration.self, in: m0) { $0.hasPrefix("generic(") }!
    let a = p.firstDeclaration(StructDeclaration.self, named: "A", in: m0)!

    // `T` occurs in the type of `generic`, which is part of the qualification of `T`.
    let t = p.types.demand(GenericParameter.user(p[f].contextParameters.types[0], .proper)).erased
    let u = p.types.demand(Struct(declaration: a)).erased
    guard let x = type(p.mangled(t)), let y = type(p.mangled(u)) else { return }

    // The second occurrence of `A` in `{T, A, A}` is mangled as a lookup.
    let single = p.types.demand(Tuple.cons(head: u, tail: .void)).erased
    let pair = p.types.demand(Tuple.cons(head: u, tail: single)).erased
    let triple = p.types.demand(Tuple.cons(head: t, tail: pair)).erased
    let m = p.mangled(triple)
    XCTAssertEqual(
      type(m), .tupleConsType(x, .tupleConsType(y, .tupleConsType(y, .void))),
      "demangling of a tuple is incorrect\n(mangled: \(m))")
  }

  /// Tests that the name of the implementation of a requirement by a generic conformance, built
  /// as the IR emitter does (i.e., from the declaration of the requirement in the trait),
  /// demangles to the entities and type arguments it denotes.
  func testImplementationOfRequirementByGenericConformance() async {
    var (p, m0) = await typeCheckedWithMinimalStandardLibrary(.init(contents: program))
    let requirement = p.findDeclaration(FunctionDeclaration.self, named: "Greeter.greet", in: m0)!
    let greet = p.findDeclaration(FunctionDeclaration.self, in: m0) {
      $0.hasPrefix("$<ConformanceDeclaration") && $0.hasSuffix(".greet")
    }!
    let c = p.cast(p.parent(containing: greet).node!, to: ConformanceDeclaration.self)!
    let a = p.firstDeclaration(StructDeclaration.self, named: "A", in: m0)!
    let t = p.types.demand(Struct(declaration: a)).erased
    let ps = p[c].contextParameters.types.map({ (x) in
      p.types.demand(GenericParameter.user(x, .proper))
    })
    guard let x = type(p.mangled(t)) else { return }

    // The second type argument is mangled as a lookup.
    let n = IRFunction.Name.implementation(requirement, c, .init(mapping: ps, to: [t, t]))
    let m = p.mangled(n)
    guard let e = entity(m) else { return }
    guard case .implementation(let y, let z, let arguments) = e else {
      return XCTFail("demangling of \(n) has the wrong structure: \(e)\n(mangled: \(m))")
    }
    XCTAssert(qualifiedName(y, describes: requirement, relativeTo: nil, in: p), "(mangled: \(m))")
    XCTAssert(component(z, describes: .node(c.erased), in: p), "(mangled: \(m))")
    XCTAssertEqual(arguments, [x, x], "type arguments are incorrect\n(mangled: \(m))")
  }

  /// An IR function name that does not contain another name, paired with a predicate that holds
  /// iff its argument has the structure of the entity to which that name should demangle.
  private typealias BaseName = (
    name: IRFunction.Name,
    isExpectedDemangling: (DemangledEntity) -> Bool
  )

  /// Returns at least one IR function name of each kind that does not contain another name, each
  /// denoting an entity of `m`, which is the module of `p` containing `program`.
  ///
  /// The types occurring in the result are demanded from `p`.
  private func baseNames(in m: Module.ID, of p: inout Program) -> [BaseName] {
    let g = p.findDeclaration(FunctionDeclaration.self, in: m) { $0.hasPrefix("g(") }!
    let origin = p.firstDeclaration(BindingDeclaration.self, named: "origin", in: m)!
    let greet = p.findDeclaration(FunctionDeclaration.self, in: m) {
      $0.hasPrefix("$<ConformanceDeclaration") && $0.hasSuffix(".greet")
    }!
    let c = p.cast(p.parent(containing: greet).node!, to: ConformanceDeclaration.self)!

    // The usings of `c` are mangled twice in the name of its implementation of `greet`: once in
    // the qualification of `greet` and once for `c` itself.
    XCTAssertEqual(
      p[c].contextParameters.usings.count, 2, "unexpected fixture: `c` should have two usings")

    // A synthetic witness constructor, which the compiler would not create: its type is `<T> E`,
    // where `E` is deliberately not applied to `T`, so that its mangling ends with a declaration
    // chain.
    let e = p.firstDeclaration(EnumDeclaration.self, named: "E", in: m)!
    let d = p[e].parameters[0]
    let t = p.types.demand(GenericParameter.user(d, .proper))
    let head = p.types.demand(Enum(declaration: e)).erased
    let synthetic = p.types.demand(UniversalType(parameters: [t], head: head))

    // The witness constructor that the back end creates for `E<T>` (see `TypeStore.constructor`),
    // whose type ends with a type lookup rather than a declaration chain once mangled.
    let application = p.types.demand(TypeApplication(abstraction: head, arguments: [t: t.erased]))
    let realistic = p.types.constructor(binding: [t], in: application.erased)

    // The closures below escape and thus can't capture `p`, which is `inout`; they capture this
    // copy instead. `p` is not modified past this point.
    let p = p
    return [
      (.lowered(g), { (x) in self.qualifiedName(x, describes: g, relativeTo: nil, in: p) }),
      (
        .initializer(origin),
        { (x) in
          guard case .initializer(let y) = x else { return false }
          return self.qualifiedName(y, describes: .init(origin), relativeTo: nil, in: p)
        }
      ),
      (
        .synthesized(g, TypeArguments()),
        { (x) in
          guard case .synthesizedFunction(let y, []) = x else { return false }
          return self.qualifiedName(y, describes: g, relativeTo: nil, in: p)
        }
      ),
      (
        .implementation(greet, c, TypeArguments()),
        { (x) in
          guard case .implementation(let y, let z, []) = x else { return false }
          return self.qualifiedName(y, describes: greet, relativeTo: nil, in: p)
            && self.component(z, describes: .node(c.erased), in: p)
        }
      ),
      (
        .typeWitnessConstructor(synthetic),
        { (x) in
          guard
            case .typeWitnessConstructor(.universalType(let ps, .enumType(let y))) = x,
            ps.count == 1, case .genericParameterUser(let z) = ps[0]
          else { return false }
          return self.qualifiedName(z, describes: .init(d), relativeTo: nil, in: p)
            && self.qualifiedName(y, describes: .init(e), relativeTo: nil, in: p)
        }
      ),
      (
        .typeWitnessConstructor(realistic),
        { (x) in
          guard
            case .typeWitnessConstructor(.universalType(let ps, let h)) = x,
            case .typeApplication(.enumType(let y), let a) = h
          else { return false }
          return (ps == [.genericParameterNth(index: 0)]) && (a == ps)
            && self.qualifiedName(y, describes: .init(e), relativeTo: nil, in: p)
        }
      ),
    ]
  }

  /// A case of `IRFunction.Name` that contains another name (i.e., `existentialized`, `slide`,
  /// `plateau`, or `applied`), together with its tag if it has one.
  ///
  /// - `name` returns the name of that case containing its argument.
  /// - `entity` returns the entity to which `name(n)` should demangle, given the entity to which
  ///   `n` demangles.
  /// - `tag` is the tag of the names returned by `name`, if any.
  private typealias Wrapper = (
    name: (IRFunction.Name) -> IRFunction.Name,
    entity: (DemangledEntity) -> DemangledEntity,
    tag: Int?
  )

  /// Returns the wrapper for `existentialized` followed by, for each `i` in `tags`, the wrappers
  /// for `slide`, `plateau`, and `applied` with tag `i`.
  private func wrappers(tags: [Int]) -> [Wrapper] {
    var result: [Wrapper] = [({ .existentialized($0) }, { .existentialized($0) }, nil)]
    for i in tags {
      result.append(({ .slide($0, i) }, { .slide($0, i) }, i))
      result.append(({ .plateau($0, i) }, { .plateau($0, i) }, i))
      result.append(({ .applied($0, i) }, { .applied($0, i) }, i))
    }
    return result
  }

  /// A program declaring a variety of entities.
  private var program: String {
    """
    // Functions returning user-defined and built-in types.
    struct A { public memberwise init }
    struct B { fun f(y: Int) -> A { A() } }
    fun g(z: Bool) -> Int { Int() }
    static fun s(x: Int) -> Bool { Bool() }

    // Other nominal types and their members.
    enum E<T> {
      case one
      case two(x: T)
    }
    trait W { type X }
    given Void is W { type X = Void }
    type Number = A

    // A generic extension.
    trait Q {}
    extension <T is Q> T { fun h() {} }
    extension <T> {Void, T} { fun i() {} }

    // A generic conformance with several constraints.
    trait P {}
    struct C<T, U> {}
    trait Greeter { fun greet() }
    given <T is P, U is Q> => C<T, U> is Greeter { fun greet() {} }

    // A function bundle.
    public fun project(x: inout Int64) auto -> Int64 {
      let   { (Int64(), ) }
      inout { Int64() }
    }

    // Local declarations and anonymous scopes.
    fun local() {
      let x = Int()
      _ = x
      let f0 = fun[](a: Void) -> Void {
        let b = Int()
        _ = b
      }
      if Bool() {
        let c = Int()
        _ = c
      }
      struct U { fun hammer() {} }
      given Number is Q {}
    }

    let origin = Int()

    """
  }

  /// The Hylo source code of synthetic function declarations, meant to be appended to `program`.
  ///
  /// These functions do not occur in `program`. Each of them has a parameter of type `A`, which is
  /// a struct declared in `program`, followed by a parameter whose label is chosen so that its
  /// mangled length, possibly followed by its first characters, reads as an operator continuing a
  /// declaration chain, right after the mangling of `A`.
  private var syntheticFunctionsCode: String {
    var source = ""
    var seen = Set<[String]>()
    for n in 1 ... 120 {
      // Strings are mangled with their length plus two.
      let d = "\(Base64VarUInt(n + 2))"
      for o in ManglingOperator.entityOperators where !o.endsDeclarationChain {
        let prefix: String
        if o.rawValue.hasPrefix(d) {
          prefix = String(o.rawValue.dropFirst(d.count))
        } else if d.hasPrefix(o.rawValue) {
          prefix = ""
        } else {
          continue
        }

        if (prefix.count > n) || !seen.insert([o.rawValue, prefix, "\(d.count)"]).inserted {
          continue
        }
        let l = prefix + String(repeating: "x", count: n - prefix.count)
        source += "fun k\(n)\(o)(a: A, \(l) b: A) {}\n"
      }
    }
    return source
  }

  /// Returns `true` iff `e` is a qualified name whose components describe `d` and the scopes
  /// containing it, assuming that a relative reference designates `r`.
  private func qualifiedName(
    _ e: DemangledEntity, describes d: DeclarationIdentity, relativeTo r: ScopeIdentity?,
    in p: Program
  ) -> Bool {
    var expected: [Component] = [.node(d.erased)]
    for s in p.scopes(from: p.parent(containing: d)) {
      expected.append(s.node.map(Component.node) ?? .file(s.file))
    }
    expected.append(.module(p.parent(containing: d).module))
    expected.reverse()

    var actual = components(of: e)
    if actual.first == .relative {
      guard let i = r.flatMap({ (s) in expected.firstIndex(of: .node(s.node!)) }) else {
        return false
      }
      expected.removeFirst(i + 1)
      actual.removeFirst()
    }

    return (actual.count == expected.count)
      && zip(actual, expected).allSatisfy({ (a, x) in component(a, describes: x, in: p) })
  }

  /// A component of a qualified name.
  private enum Component: Equatable {

    /// A module.
    case module(Module.ID)

    /// A source file.
    case file(SourceFile.ID)

    /// A scope or declaration.
    case node(AnySyntaxIdentity)

  }

  /// Returns `true` iff `a` describes `x`.
  private func component(_ a: DemangledEntity, describes x: Component, in p: Program) -> Bool {
    switch x {
    case .module(let m):
      return a == .module(p[m].name.description)

    case .file(let f):
      switch p[f].source.name {
      case .local(let u):
        return a == .sourceFile(u.deletingPathExtension().lastPathComponent)
      case .virtual(let u):
        return a == .virtualSourceFile(u.absoluteString)
      }

    case .node(let n):
      return component(a, describes: n, in: p)
    }
  }

  /// Returns `true` iff `a` describes `n`, which is a scope or a declaration.
  private func component(
    _ a: DemangledEntity, describes n: AnySyntaxIdentity, in p: Program
  ) -> Bool {
    switch p.tag(of: n) {
    case Block.self, If.self:
      return a == .anonymousScope(UInt64(n.bits))

    case BindingDeclaration.self:
      let b = BindingDeclaration.ID(uncheckedFrom: n)
      guard case .binding(let names) = a else { return false }
      return names.map(\.identifier) == p.names(introducedBy: b).map(\.identifier)

    case ConformanceDeclaration.self:
      guard case .conformanceDeclaration(_, let usings) = a else { return false }
      let c = ConformanceDeclaration.ID(uncheckedFrom: n)
      return self.usings(usings, describe: p[c].contextParameters.usings, of: n, in: p)

    case ExtensionDeclaration.self:
      guard case .extensionDeclaration(_, let usings) = a else { return false }
      let x = ExtensionDeclaration.ID(uncheckedFrom: n)
      return self.usings(usings, describe: p[x].contextParameters.usings, of: n, in: p)

    case FunctionDeclaration.self:
      let f = FunctionDeclaration.ID(uncheckedFrom: n)
      guard let expected = p.name(of: f) else { return a == .anonymousScope(UInt64(n.bits)) }
      guard
        case .functionDeclaration(let name, let t, let isStatic) = a,
        let inputs = arrowInputs(t)
      else { return false }
      let labels = p[f].parameters.map({ (x) in p[x].label?.value })
      return (name.identifier == expected.identifier) && (name.notation == expected.notation)
        && (isStatic == p.isStatic(f)) && (inputs.suffix(labels.count).map(\.label) == labels)

    case FunctionBundleDeclaration.self:
      let f = FunctionBundleDeclaration.ID(uncheckedFrom: n)
      guard case .functionBundleDeclaration(let name, _) = a else { return false }
      return name.identifier == p.name(of: f).identifier

    case VariantDeclaration.self:
      return a == .variant(p[VariantDeclaration.ID(uncheckedFrom: n)].effect.value)

    default:
      let d = DeclarationIdentity(uncheckedFrom: n)
      return p.name(of: d).map({ (x) in a == .scope(x.identifier) }) ?? false
    }
  }

  /// Returns `true` iff `usings` describe `expected`, which are the usings of `n`.
  private func usings(
    _ usings: [DemangledEntity], describe expected: [DeclarationIdentity],
    of n: AnySyntaxIdentity, in p: Program
  ) -> Bool {
    let s = ScopeIdentity(uncheckedFrom: n)
    return (usings.count == expected.count)
      && zip(usings, expected).allSatisfy({ (u, d) in
        qualifiedName(u, describes: d, relativeTo: s, in: p)
      })
  }

  /// Returns the parameters of `t` if it is an arrow, possibly under universal quantification
  /// and implication.
  private func arrowInputs(_ t: DemangledType) -> [DemangledType.Parameter]? {
    switch t {
    case .arrow(_, _, _, let inputs, _):
      return inputs
    case .universalType(_, let h), .implication(_, let h):
      return arrowInputs(h)
    default:
      return nil
    }
  }

  /// Returns the components of the qualified name `e`, from outermost to innermost.
  private func components(of e: DemangledEntity) -> [DemangledEntity] {
    if case .qualified(let h, let q) = e {
      return components(of: q) + [h]
    } else {
      return [e]
    }
  }

  /// Asserts that `n` demangles to `expected`.
  private func assertDemangling(
    of n: IRFunction.Name, is expected: DemangledEntity, in p: Program,
    file: StaticString = #filePath, line: UInt = #line
  ) {
    let m = p.mangled(n)
    guard let e = entity(m, file: file, line: line) else { return }
    XCTAssertEqual(
      e, expected, "demangling of \(n) is incorrect\n(mangled: \(m))", file: file, line: line)
  }

  /// Returns the entity demangled from `m`, failing the current test if `m` does not demangle to
  /// an entity without error.
  private func entity(
    _ m: String, file: StaticString = #filePath, line: UInt = #line
  ) -> DemangledEntity? {
    assertDemanglingIsOk(mangled: m, file: file, line: line)
    if case .entity(let e) = DemangledSymbol(m) {
      return e
    } else {
      XCTFail(
        "expected an entity, got: \(DemangledSymbol(m))\n(mangled: \(m))", file: file, line: line)
      return nil
    }
  }

  /// Returns the type demangled from `m`, failing the current test if `m` does not demangle to a
  /// type without error.
  private func type(
    _ m: String, file: StaticString = #filePath, line: UInt = #line
  ) -> DemangledType? {
    assertDemanglingIsOk(mangled: m, file: file, line: line)
    if case .type(let t) = DemangledSymbol(m) {
      return t
    } else {
      XCTFail(
        "expected a type, got: \(DemangledSymbol(m))\n(mangled: \(m))", file: file, line: line)
      return nil
    }
  }

}
