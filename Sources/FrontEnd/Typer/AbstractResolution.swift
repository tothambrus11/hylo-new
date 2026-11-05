import Utilities

/// A sound pre-check for implicit resolution based on an abstract least model of the givens.
///
/// Givens are read as definite Horn clauses over first-order terms: a given of type
/// `<X...> A1, ..., An ==> H` is the clause `H :- A1, ..., An`, whose variables are `X...`.
/// Implicit resolution is SLD resolution over these clauses (with a size-ordered search), so any
/// type it can derive is in the least Herbrand model of the clauses. That model is infinite in
/// general, so we compute an over-approximation by bottom-up (Datalog-style) saturation in the
/// domain of depth-k truncated terms, where subterms below depth `k` are replaced by `⊤`
/// (Sato & Tamaki's depth-k abstraction). The abstract model is finite, so saturation terminates.
///
/// If a query does not unify with any atom of the abstract model, then resolution must fail and
/// can be skipped. The converse does not hold: a query matching the abstract model may still be
/// underivable (false negatives are allowed, false positives are not).
///
/// Coercions break the syntactic view of matching (two types may be "equal" without unifying),
/// so the analysis gives up on any set of givens containing a potential source of coercions
/// (i.e., a given whose head is an equality witness or a bare variable).
internal struct AbstractResolutionModel {

  /// A key identifying a term constructor.
  internal enum Key: Hashable {

    /// A nominal type constructor or rigid type (struct, trait, skolem, machine type, ...).
    case type(AnyTypeIdentity)

    /// The constructor of a non-empty tuple, applied to its head and tail.
    case cons

    /// The empty tuple.
    case empty

    /// An equality witness.
    case equality

  }

  /// A depth-k abstraction of a type.
  internal indirect enum Term: Hashable {

    /// Any term.
    case top

    /// A variable, local to a clause or a fact.
    case variable(Int)

    /// The application of a constructor to zero or more arguments.
    case node(Key, [Term])

    /// The key of the term's head constructor, if any.
    var key: Key? {
      if case .node(let k, _) = self { k } else { nil }
    }

  }

  /// A definite Horn clause `head :- premises`.
  internal struct Clause {

    /// The conclusion of the clause.
    let head: Term

    /// The premises of the clause.
    let premises: [Term]

  }

  /// The depth at which terms are truncated.
  internal let depth: Int

  /// The maximum number of facts before the analysis gives up.
  internal let factLimit: Int

  /// The clauses of the model.
  private(set) var clauses: [Clause] = []

  /// The facts of the model, bucketed by the key of their head constructor.
  private(set) var facts: [Key: [Term]] = [:]

  /// The number of facts in the model.
  private(set) var factCount: Int = 0

  /// `true` iff the analysis can't be used to refute queries.
  private(set) var isInconclusive: Bool = false

  /// Statistics: the number of clause applications attempted during saturation.
  private(set) var work: Int = 0

  /// Creates an empty model.
  internal init(depth: Int, factLimit: Int = 20_000) {
    self.depth = depth
    self.factLimit = factLimit
  }

  /// Marks the model inconclusive.
  internal mutating func giveUp() {
    isInconclusive = true
  }

  /// Adds `c` to the clauses of this model. Call `saturate` once all clauses have been added.
  internal mutating func add(_ c: Clause) {
    switch c.head {
    case .top, .variable:
      isInconclusive = true
    case .node(.equality, _):
      isInconclusive = true
    case .node:
      // Equalities are derived by built-in givens (reflexivity, symmetry, transitivity) that are
      // not modeled, so equality premises are assumed to hold (over-approximation).
      let ps = c.premises.filter({ (p) in p.key != .equality })
      clauses.append(.init(head: c.head, premises: ps))
    }
  }

  /// Returns `true` if `query` may be derivable, `false` if it is definitely not derivable.
  internal func mayDerive(_ query: Term) -> Bool {
    if isInconclusive { return true }
    guard let k = query.key, k != .equality else { return true }
    for f in facts[k] ?? [] {
      var s: [Int: Term] = [:]
      // Variables of facts are renamed apart from those of the query by offsetting them.
      let g = f.isGround ? f : f.offsettingVariables(by: 1 << 20)
      if Self.unify(query, g, &s) { return true }
    }
    return false
  }

  /// Computes the least fixed point of the clauses, assuming that the current facts are closed
  /// under the clauses before `firstNew`.
  ///
  /// The algorithm is semi-naive evaluation: after the first round, a clause instance is only
  /// considered if at least one of its premises is matched by a fact derived in the last round.
  /// Buckets are append-only, so a "generation" is a prefix of each bucket.
  internal mutating func saturate(from firstNew: Int = 0) {
    if isInconclusive { return }

    // Clauses depending on each key.
    var dependents: [Key: [Int]] = [:]
    for (i, c) in clauses.enumerated() {
      for k in Set(c.premises.compactMap(\.key)) { dependents[k, default: []].append(i) }
    }

    // Round 0: new clauses against all facts.
    var lo: [Key: Int] = facts.mapValues(\.count)  // End of the "old" prefix.
    var hi = lo                                     // End of the "delta" segment.
    for i in firstNew ..< clauses.count {
      if !run(clauses[i], delta: nil, lo: lo, hi: hi) { return }
    }

    while true {
      // The delta of this round is what has been added since the last round.
      lo = hi
      hi = facts.mapValues(\.count)
      var touched: Set<Int> = []
      for (k, n) in hi where n > (lo[k] ?? 0) {
        for i in dependents[k] ?? [] { touched.insert(i) }
      }
      if touched.isEmpty { return }
      for i in touched.sorted() {
        let c = clauses[i]
        for (j, p) in c.premises.enumerated() {
          guard let k = p.key, (hi[k] ?? 0) > (lo[k] ?? 0) else { continue }
          if !run(c, delta: j, lo: lo, hi: hi) { return }
        }
      }
    }
  }

  /// Applies `c`, using only facts in the delta segment for premise `delta` (if any), facts in the
  /// old prefix for premises before `delta`, and old or delta facts for those after. Returns
  /// `false` iff the analysis gave up.
  private mutating func run(_ c: Clause, delta: Int?, lo: [Key: Int], hi: [Key: Int]) -> Bool {
    var result: [Term] = []
    var s: [Int: Term] = [:]
    match(c.premises[...], 0, delta, lo, hi, &s, c, &result)
    for h in result {
      _ = insert(h)
      if factCount > factLimit {
        isInconclusive = true
        return false
      }
    }
    return true
  }

  /// Extends `result` with the instances of `c.head` derivable by matching `ps`, whose first
  /// element is the `j`-th premise of `c`, against the facts selected by `delta`, `lo`, and `hi`.
  private mutating func match(
    _ ps: ArraySlice<Term>, _ j: Int, _ delta: Int?, _ lo: [Key: Int], _ hi: [Key: Int],
    _ s: inout [Int: Term], _ c: Clause, _ result: inout [Term]
  ) {
    guard let p = ps.first else {
      result.append(canonical(truncated(Self.applying(s, to: c.head), at: depth)))
      return
    }

    // A premise that is not headed by a constructor may match anything; skip it.
    guard let k = p.key else {
      match(ps.dropFirst(), j + 1, delta, lo, hi, &s, c, &result)
      return
    }

    let bucket = facts[k] ?? []
    let range: Range<Int>
    switch delta {
    case .some(let d) where j < d: range = 0 ..< (lo[k] ?? 0)
    case .some(let d) where j == d: range = (lo[k] ?? 0) ..< (hi[k] ?? 0)
    default: range = 0 ..< min(hi[k] ?? 0, bucket.count)
    }
    for f in bucket[range] {
      work += 1
      var t = s
      let g = f.isGround ? f : f.offsettingVariables(by: (1 << 20) + (work << 8))
      if Self.unify(p, g, &t) {
        match(ps.dropFirst(), j + 1, delta, lo, hi, &t, c, &result)
      }
    }
  }

  /// Inserts `f` into the facts unless it is subsumed by an existing fact, returning `true` iff
  /// the model has changed.
  private mutating func insert(_ f: Term) -> Bool {
    let k = f.key!
    var bucket = facts[k] ?? []
    if bucket.contains(where: { (g) in Self.subsumes(g, f) }) { return false }
    bucket.append(f)
    factCount += 1
    facts[k] = bucket
    return true
  }

  // MARK: Term algebra

  /// Returns `t` with subterms deeper than `d` replaced by `⊤`.
  internal func truncated(_ t: Term, at d: Int) -> Term {
    if d <= 0 { return .top }
    if case .node(let k, let xs) = t {
      return .node(k, xs.map({ (x) in truncated(x, at: d - 1) }))
    }
    return t
  }

  /// Returns `t` with its variables renamed in order of first occurrence.
  internal func canonical(_ t: Term) -> Term {
    var m: [Int: Int] = [:]
    func go(_ t: Term) -> Term {
      switch t {
      case .top: return .top
      case .variable(let v):
        if let w = m[v] { return .variable(w) }
        let w = m.count
        m[v] = w
        return .variable(w)
      case .node(let k, let xs): return .node(k, xs.map(go))
      }
    }
    return go(t)
  }

  /// Returns `t` with the substitution `s` applied.
  internal static func applying(_ s: [Int: Term], to t: Term) -> Term {
    switch t {
    case .top: return .top
    case .variable(let v):
      if let u = s[v] { return applying(s, to: u) }
      return t
    case .node(let k, let xs):
      return .node(k, xs.map({ (x) in applying(s, to: x) }))
    }
  }

  /// Resolves the binding of `t` in `s`.
  private static func walk(_ t: Term, _ s: [Int: Term]) -> Term {
    var t = t
    while case .variable(let v) = t, let u = s[v] { t = u }
    return t
  }

  /// Returns `true` iff `a` and `b` are unifiable, extending `s`.
  ///
  /// `⊤` unifies with anything. There is no occurs check, mirroring the concrete unifier.
  internal static func unify(_ a: Term, _ b: Term, _ s: inout [Int: Term]) -> Bool {
    let x = walk(a, s)
    let y = walk(b, s)
    switch (x, y) {
    case (.top, _), (_, .top):
      return true
    case (.variable(let v), .variable(let w)) where v == w:
      return true
    case (.variable(let v), _):
      s[v] = y
      return true
    case (_, .variable(let w)):
      s[w] = x
      return true
    case (.node(let k, let xs), .node(let l, let ys)):
      if k != l || xs.count != ys.count { return false }
      for (u, v) in zip(xs, ys) where !unify(u, v, &s) { return false }
      return true
    }
  }

  /// Returns `true` iff every instance of `specific` is an instance of `general`.
  internal static func subsumes(_ general: Term, _ specific: Term) -> Bool {
    var s: [Int: Term] = [:]
    func go(_ g: Term, _ t: Term) -> Bool {
      switch (g, t) {
      case (.top, _):
        return true
      case (.variable(let v), _):
        if let u = s[v] { return u == t }
        s[v] = t
        return true
      case (.node(let k, let xs), .node(let l, let ys)):
        if k != l || xs.count != ys.count { return false }
        for (a, b) in zip(xs, ys) where !go(a, b) { return false }
        return true
      default:
        return false
      }
    }
    return go(general, specific)
  }

}

extension AbstractResolutionModel.Term {

  /// `true` iff `self` contains no variable.
  fileprivate var isGround: Bool {
    switch self {
    case .top: return true
    case .variable: return false
    case .node(_, let xs): return xs.allSatisfy(\.isGround)
    }
  }

  /// Returns `self` with every variable `v` renamed to `v + n`.
  fileprivate func offsettingVariables(by n: Int) -> Self {
    switch self {
    case .top: return .top
    case .variable(let v): return .variable(v + n)
    case .node(let k, let xs): return .node(k, xs.map({ (x) in x.offsettingVariables(by: n) }))
    }
  }

}

extension TypeStore {

  /// Returns the abstraction of `t` in which the generic parameters in `bound` and the type
  /// variables are replaced by abstract variables, and in which types that are not first-order
  /// terms are replaced by `⊤`.
  internal func abstraction(
    of t: AnyTypeIdentity, binding bound: [GenericParameter.ID: Int],
    variables: inout [AnyTypeIdentity: Int]
  ) -> AbstractResolutionModel.Term {
    if t.isVariable {
      if let v = variables[t] { return .variable(v) }
      let v = (1 << 30) + variables.count
      variables[t] = v
      return .variable(v)
    }

    switch self[t] {
    case let u as GenericParameter:
      _ = u
      if let v = bound[GenericParameter.ID(uncheckedFrom: t)] { return .variable(v) }
      return .node(.type(t), [])
    case is Struct, is Enum, is Trait, is MachineType:
      return .node(.type(t), [])
    case let u as TypeApplication:
      switch self[u.abstraction] {
      case is Struct, is Enum, is Trait:
        let xs = u.arguments.values.map { (a) in
          abstraction(of: a, binding: bound, variables: &variables)
        }
        return .node(.type(u.abstraction), xs)
      default:
        return .top
      }
    case let u as Tuple:
      switch u {
      case .empty:
        return .node(.empty, [])
      case .cons(let h, let r):
        return .node(.cons, [
          abstraction(of: h, binding: bound, variables: &variables),
          abstraction(of: r, binding: bound, variables: &variables),
        ])
      }
    case let u as EqualityWitness:
      return .node(.equality, [
        abstraction(of: u.lhs, binding: bound, variables: &variables),
        abstraction(of: u.rhs, binding: bound, variables: &variables),
      ])
    case let u as TypeAlias:
      return abstraction(of: u.aliasee, binding: bound, variables: &variables)
    default:
      return .top
    }
  }

}
