/// Research instrumentation: a textual, identity-independent dump of the results of type checking.
extension Program {

  /// Returns one line per typed syntax tree, name binding, and witness table of `m`, sorted.
  ///
  /// The dump shows types and declaration references textually so that it does not depend on the
  /// order in which types were interned. Two runs of the type checker computing the same
  /// elaboration produce the same dump.
  public func semanticDump(of m: Module.ID) -> [String] {
    var lines: [String] = []
    for (f, s) in self[m].sources.values.enumerated() {
      for (n, t) in s.syntaxToType {
        lines.append("\(f):\(n) : \(show(t))")
      }
      for (n, r) in s.nameToDeclaration {
        lines.append("\(f):\(n) -> \(show(r))")
      }
      for (n, w) in s.witnessTables {
        lines.append("\(f):\(n) witness \(show(w.concept))")
        let e = w.researchEntries
        for (r, x) in e.conformances { lines.append("\(f):\(n) witness.c\(r) = \(show(x))") }
        for (r, x) in e.types { lines.append("\(f):\(n) witness.t\(r) = \(show(x))") }
        for (r, x) in e.members { lines.append("\(f):\(n) witness.m\(r) = \(show(x))") }
      }
    }
    return lines.sorted()
  }

}
