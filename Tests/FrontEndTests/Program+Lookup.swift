@testable import FrontEnd

extension Program {

  /// Finds the first top-level declaration of `m` whose debug name is `n`, returning its identity,
  /// or `nil` if no such declaration exists.
  ///
  /// The debug name of a declaration (see `Program.debugName(of:)`) is not its name: it is
  /// qualified by the debug names of the declarations that contain it (e.g., `Greeter.greet`) and
  /// describes a declaration that does not introduce exactly one name by its tag (e.g.,
  /// `$<ConformanceDeclaration at ...>`).
  func firstTopLevelDeclaration(named n: String, in m: Module.ID) -> DeclarationIdentity? {
    self[m].topLevelDeclarations.first { (d) in debugName(of: d) == n }
  }

  /// Finds the first declaration of `m` of type `t` whose debug name is `n`, returning its
  /// identity, or `nil` if no such declaration exists.
  func findDeclaration(
    _ t: any Syntax.Type, named n: String, in m: Module.ID
  ) -> DeclarationIdentity? {
    findDeclaration(t, in: m) { $0 == n }
  }

  /// Finds the first declaration of `m` of type `t` whose debug name satisfies `p`, returning its
  /// identity, or `nil` if no such declaration exists.
  func findDeclaration(
    _ t: any Syntax.Type, in m: Module.ID,
    nameMatching p: @escaping (String) -> Bool = { _ in true }
  ) -> DeclarationIdentity? {
    let hasMatchingName = SyntaxFilter.satisfies { (n) in
      p(debugName(of: DeclarationIdentity(uncheckedFrom: n)))
    }
    return select(from: m, .and(.tag(t), hasMatchingName))
      .first.map(DeclarationIdentity.init(uncheckedFrom:))
  }

  /// Finds the first declaration of `m` of type `t` whose debug name is `n`, returning its
  /// identity, or `nil` if no such declaration exists.
  func firstDeclaration<T: Declaration>(
    _ t: T.Type, named n: String, in m: Module.ID
  ) -> T.ID? {
    firstDeclaration(t, in: m) { $0 == n }
  }

  /// Finds the first declaration of `m` of type `t` whose debug name satisfies `p`, returning its
  /// identity, or `nil` if no such declaration exists.
  func firstDeclaration<T: Declaration>(
    _ t: T.Type, in m: Module.ID, nameMatching p: @escaping (String) -> Bool = { _ in true }
  ) -> T.ID? {
    findDeclaration(t, in: m, nameMatching: p).map({ (d) in T.ID(uncheckedFrom: d.erased) })
  }

}
