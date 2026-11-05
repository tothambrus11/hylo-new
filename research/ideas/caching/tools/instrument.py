"""Adds research counters to the private clone in research/ideas/caching/hylo (never hylo-new)."""
import sys
root = sys.argv[1]
assert "ideas/caching/hylo" in root


def edit(path, old, new, count=1):
    s = open(path).read()
    n = s.count(old)
    assert n == count, (path, old[:70], n)
    s = s.replace(old, new)
    open(path, "w").write(s)


C = root + "/Typer/TyperCounters.swift"
edit(C, "  /// Resets all counters.\n  public static func reset() { values = [:] }",
"""  /// Hashes seen per duplicate-detection counter.
  nonisolated(unsafe) public static var seen: [String: Set<Int>] = [:]

  /// Records key `h` under counter `k`, bumping `k.distinct` or `k.repeat`.
  public static func dup(_ k: StaticString, _ h: Int) {
    if !enabled { return }
    let key = "\\(k)"
    if seen[key, default: []].insert(h).inserted {
      values[key + ".distinct", default: 0] += 1
    } else {
      values[key + ".repeat", default: 0] += 1
    }
  }

  /// Resets all counters.
  public static func reset() { values = [:]; seen = [:] }""")

T = root + "/Typer/Typer.swift"
edit(T, "  /// Returns `true` iff there is a declaration introducing an implicit that is being typed.\n",
"""  /// Instrumentation: a hash of the implicit declarations on the stack.
  private func implicitStackKey() -> Int {
    var h = Hasher()
    for d in declarationsOnStack where program.isImplicit(d) { h.combine(d) }
    return h.finalize() &+ declarationsOnStack.filter(program.isImplicit).count
  }

  /// Returns `true` iff there is a declaration introducing an implicit that is being typed.
""")

P = root + "/Program.swift"
edit(P, """  internal mutating func initializeStandardLibraryCaches() {
    for n in Program.StandardLibraryEntity.allCases {""",
"""  internal mutating func initializeStandardLibraryCaches() {
    let t0 = TyperCounters.enabled ? TyperClock.now() : 0
    defer {
      if TyperCounters.enabled {
        TyperCounters.bump("stdcache.micros", by: Int((TyperClock.now() - t0) * 1000))
        if let m = identity(module: Module.standardLibraryName) {
          TyperCounters.bump("stdcache.nodes", by: modules.values[m].syntax.count)
        }
      }
    }
    for n in Program.StandardLibraryEntity.allCases {""")

# summon miss reasons and stack-keyed duplicates
edit(T, """    let result: [SummonResult]

    // If there aren't any givens in `scopeOfUse`, just summon in the parent scope.
    if givens(lexicallyIn: scopeOfUse).isEmpty, let p = program.parent(containing: scopeOfUse) {
      result = summon(t, in: p)
    }""",
"""    let result: [SummonResult]
    let instr = TyperCounters.enabled
      && !(givens(lexicallyIn: scopeOfUse).isEmpty && program.parent(containing: scopeOfUse) != nil)
    let t0 = instr ? TyperClock.now() : 0
    let why = !instr ? 0 : (t[.hasVariable] ? 1 : (hasImplicitOnStack() ? 2 : 3))
    if why == 1 {
      TyperCounters.bump("summon.miss.var")
      var h = Hasher(); h.combine(scopeOfUse); h.combine(t); h.combine(implicitStackKey())
      TyperCounters.dup("summon.varkey", h.finalize())
    } else if why == 2 {
      TyperCounters.bump("summon.miss.stack")
      var h = Hasher(); h.combine(scopeOfUse); h.combine(t); h.combine(implicitStackKey())
      TyperCounters.dup("summon.stackkey", h.finalize())
      var h2 = Hasher(); h2.combine(scopeOfUse); h2.combine(t)
      TyperCounters.dup("summon.stackfree", h2.finalize())
    } else if why == 3 {
      TyperCounters.bump("summon.miss.cold")
    }
    defer {
      if why != 0 {
        let us = Int((TyperClock.now() - t0) * 1000)
        switch why {
        case 1: TyperCounters.bump("summon.miss.var.us", by: us)
        case 2: TyperCounters.bump("summon.miss.stack.us", by: us)
        default: TyperCounters.bump("summon.miss.cold.us", by: us)
        }
      }
    }

    // If there aren't any givens in `scopeOfUse`, just summon in the parent scope.
    if givens(lexicallyIn: scopeOfUse).isEmpty, let p = program.parent(containing: scopeOfUse) {
      result = summon(t, in: p)
    }""")

# canDeriveCoercions
edit(T, """    let memoizable = environment.givens.isEmpty && p.isClosed
    if memoizable, let memoized = cache.scopeToPotentialCoercions[scopeOfUse]?[p] {
      return memoized
    }
""", """    let memoizable = environment.givens.isEmpty && p.isClosed
    TyperCounters.bump("cdc.calls")
    if memoizable, let memoized = cache.scopeToPotentialCoercions[scopeOfUse]?[p] {
      TyperCounters.bump("cdc.memoHit")
      return memoized
    }
    if TyperCounters.enabled {
      if !environment.givens.isEmpty { TyperCounters.bump("cdc.miss.env") }
      else if !p.isClosed { TyperCounters.bump("cdc.miss.open") }
      else if hasImplicitOnStack() { TyperCounters.bump("cdc.miss.stack") }
      else { TyperCounters.bump("cdc.miss.cold") }
      if !declarationsOnStack.isEmpty { TyperCounters.bump("cdc.declOnStack") }
    }
    let cdcT0 = TyperCounters.enabled ? TyperClock.now() : 0
    defer {
      if TyperCounters.enabled {
        TyperCounters.bump("cdc.us", by: Int((TyperClock.now() - cdcT0) * 1000))
      }
    }
""")
edit(T, """      sources = Array(givens(visibleFrom: scopeOfUse).joined())
    }
    for g in chain(environment.givens, sources)  {""", """      sources = Array(givens(visibleFrom: scopeOfUse).joined())
      TyperCounters.bump("cdc.scanPath")
    }
    TyperCounters.bump("cdc.sourcesScanned", by: sources.count)
    TyperCounters.bump("cdc.envScanned", by: environment.givens.count)
    for g in chain(environment.givens, sources)  {""")

# canDeriveCoercion
edit(T, """    if let memoized = cache.canDeriveCoercion[g]?[p] { return memoized }

    // Do not memoize variable-bearing keys or results computed while givens are on stack.
    // Such queries may yield different results in the future.
    let memoizable = p.isClosed && !hasImplicitOnStack()

    let t = declaredType(of: g)
    let u = program.types.contextAndHead(t)
""", """    TyperCounters.bump("cd1.calls")
    if let memoized = cache.canDeriveCoercion[g]?[p] {
      TyperCounters.bump("cd1.memoHit")
      return memoized
    }

    // Do not memoize variable-bearing keys or results computed while givens are on stack.
    // Such queries may yield different results in the future.
    let memoizable = p.isClosed && !hasImplicitOnStack()

    let t = declaredType(of: g)
    let u = program.types.contextAndHead(t)
    if TyperCounters.enabled {
      if u.context.parameters.contains(where: { (p) in p == u.head }) {
        TyperCounters.bump("cd1.kind.any")
      } else if program.types.cast(u.head, to: EqualityWitness.self) != nil {
        TyperCounters.bump("cd1.kind.eq")
      } else {
        TyperCounters.bump("cd1.kind.none")
      }
      if !p.isClosed { TyperCounters.bump("cd1.unmemo.open") }
      else if !memoizable { TyperCounters.bump("cd1.unmemo.stack") }
    }
""")

# resolve(memberOf:)
edit(T, """    var candidates: [NameResolutionCandidate] = []
    let (type: r, isStatic: s) = qualificationForSelection(on: q)
""", """    var candidates: [NameResolutionCandidate] = []
    let (type: r, isStatic: s) = qualificationForSelection(on: q)
    if TyperCounters.enabled {
      TyperCounters.bump("member.calls")
      if q[.hasVariable] { TyperCounters.bump("member.open") }
      var h = Hasher(); h.combine(n); h.combine(q); h.combine(scopeOfUse); h.combine(declarationsOnStack)
      TyperCounters.dup("member.key", h.finalize())
      var h2 = Hasher(); h2.combine(n); h2.combine(q); h2.combine(scopeOfUse.file)
      h2.combine(declarationsOnStack)
      TyperCounters.dup("member.keyfile", h2.finalize())
      if declarationsOnStack.isEmpty { TyperCounters.bump("member.stackEmpty") }
    }
    let memberT0 = TyperCounters.enabled ? TyperClock.now() : 0
    defer {
      if TyperCounters.enabled {
        TyperCounters.bump("member.us", by: Int((TyperClock.now() - memberT0) * 1000))
      }
    }
""")

# trait member lookup
edit(T, """    for d in traits(visibleFrom: scopeOfUse) {
      let ms = lookup(name, lexicallyIn: .init(node: d)).filter(resolvableWithQualification(_:))
      if !ms.isEmpty {""", """    TyperCounters.bump("traitlookup.calls")
    for d in traits(visibleFrom: scopeOfUse) {
      TyperCounters.bump("traitlookup.scanned")
      let ms = lookup(name, lexicallyIn: .init(node: d)).filter(resolvableWithQualification(_:))
      if !ms.isEmpty {
        TyperCounters.bump("traitlookup.hit")""")

# unqualified lookup
edit(T, """  ) -> [DeclarationIdentity] {
    var result: [DeclarationIdentity] = []

    /// Adds the contents of `ds` to `result` if either `result` is empty or all elements in `ds`""",
"""  ) -> [DeclarationIdentity] {
    var result: [DeclarationIdentity] = []
    if TyperCounters.enabled {
      var h = Hasher(); h.combine(name); h.combine(scopeOfUse); h.combine(bound)
      TyperCounters.dup("unqual.key", h.finalize())
    }

    /// Adds the contents of `ds` to `result` if either `result` is empty or all elements in `ds`""")

# declaredType(of: Given) nested
edit(T, """    case .nested(let p, let d):
      let c = contextOfSelf(in: p)""", """    case .nested(let p, let d):
      TyperCounters.bump("given.nestedType")
      let c = contextOfSelf(in: p)""")

# applies
edit(T, """    let key = Memos.ExtensionAndType(d, t)
    if let memoized = cache.scopeToExtensionApplies[scopeOfUse]?[key] { return memoized }
""", """    let key = Memos.ExtensionAndType(d, t)
    TyperCounters.bump("applies.slow")
    if let memoized = cache.scopeToExtensionApplies[scopeOfUse]?[key] {
      TyperCounters.bump("applies.memoHit")
      return memoized
    }
""")

# givens(visibleFrom:)
edit(T, """  internal mutating func givens(visibleFrom scopeOfUse: ScopeIdentity) -> [[Given]] {
    var gs: [[Given]] = []
""", """  internal mutating func givens(visibleFrom scopeOfUse: ScopeIdentity) -> [[Given]] {
    var gs: [[Given]] = []
    TyperCounters.bump("givensVisible.calls")
    defer { TyperCounters.bump("givensVisible.items", by: gs.reduce(0, { $0 + $1.count })) }
""")
print("ok")
