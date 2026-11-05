# Counter-only instrumentation of the private copy (no behavioral change).
import re, sys
root = "/home/hylo/hylo-tc/research/ideas/redundancy/hylo/Sources/FrontEnd/"
def edit(path, old, new, count=1):
    p = root + path; s = open(p).read()
    assert s.count(old) == count, (path, old[:60], s.count(old))
    s = s.replace(old, new); open(p, "w").write(s)

# A. canDeriveCoercions scan statistics.
edit("Typer/Typer.swift", """      sources = Array(givens(visibleFrom: scopeOfUse).joined())
    }
""", """      sources = Array(givens(visibleFrom: scopeOfUse).joined())
    }
    if TyperCounters.enabled {
      TyperCounters.bump("cdc.calls")
      if TyperExperiments.index && cache.scopeToGivenIndex[scopeOfUse] != nil && !declarationsOnStack.isEmpty {
        TyperCounters.bump("cdc.scanIndexCached")
      }
      if sources.count > 0 && !(TyperExperiments.index && declarationsOnStack.isEmpty) {
        TyperCounters.bump("cdc.scanPath")
        TyperCounters.bump("cdc.scanGivens", by: sources.count)
        if !declarationsOnStack.isEmpty { TyperCounters.bump("cdc.scanOnStack") }
        for g in sources {
          var inner = g
          while case .nested(_, let h) = inner { inner = h }
          var t: AnyTypeIdentity? = nil
          switch inner {
          case .user(let d): t = program[d.module].type(assignedTo: d)
          case .recursive(let u), .assumed(_, let u): t = u
          default: t = nil
          }
          if let t {
            TyperCounters.bump("cdc.scanTyped")
            let (c, h) = program.types.contextAndHead(t)
            if c.parameters.contains(where: { (p) in p.erased == h }) || program.types.isEquality(h) {
              TyperCounters.bump("cdc.scanSources")
            }
          }
        }
      } else {
        TyperCounters.bump("cdc.indexPath")
        TyperCounters.bump("cdc.indexSources", by: sources.count)
      }
    }
""")
edit("Typer/Typer.swift", """    if memoizable, let memoized = cache.scopeToPotentialCoercions[scopeOfUse]?[p] {
      return memoized
    }
""", """    if memoizable, let memoized = cache.scopeToPotentialCoercions[scopeOfUse]?[p] {
      TyperCounters.bump("cdc.memoHit")
      return memoized
    }
""")
# B. canDeriveCoercion(applying:)
edit("Typer/Typer.swift", """    if let memoized = cache.canDeriveCoercion[g]?[p] { return memoized }
""", """    TyperCounters.bump("cdc.applyCalls")
    if let memoized = cache.canDeriveCoercion[g]?[p] { TyperCounters.bump("cdc.applyMemoHit"); return memoized }
""")
# C. unification
edit("Types/TypeStore.swift", """    let a = ss[lhs]
    let b = ss[rhs]

    // The two types are trivially equal?
""", """    let a = ss[lhs]
    let b = ss[rhs]
    TyperCounters.bump("unify.calls")

    // The two types are trivially equal?
""")
edit("Types/TypeStore.swift", """    let result: Bool
    if TyperExperiments.unify {""", """    let result: Bool
    TyperCounters.bump("unify.shape")
    if TyperExperiments.unify {""")
# D. loopcheck
edit("Typer/Typer.swift", """    if TyperExperiments.loopcheck && !ancestors.isEmpty {
      let u""", """    if TyperExperiments.loopcheck && !ancestors.isEmpty {
      TyperCounters.bump("loopcheck.checks")
      TyperCounters.bump("loopcheck.reifies", by: ancestors.count + 1)
      let u""")
edit("Typer/Typer.swift", """        if TyperExperiments.loopcheck {
          e.ancestry[environment.nextGivenIdentifier] = ancestors.appending(queried)""",
"""        if TyperExperiments.loopcheck {
          TyperCounters.bump("loopcheck.records")
          TyperCounters.bump("loopcheck.recordedLen", by: ancestors.count + 1)
          e.ancestry[environment.nextGivenIdentifier] = ancestors.appending(queried)""")
# E. absmodel queries
edit("Typer/Typer.swift", """    guard let m = abstractModel(visibleFrom: scopeOfUse) else { return true }
""", """    guard let m = abstractModel(visibleFrom: scopeOfUse) else { return true }
    TyperCounters.bump("absmodel.queries")
    if m.isInconclusive { TyperCounters.bump("absmodel.queriesInconclusive") }
""")
# E2. after refutation check in indexedSummon: threads index would form for refuted goals (only if index cached)
edit("Typer/Typer.swift", """    if TyperExperiments.absmodel && !u.isVariable && !mayDerive(u, in: scopeOfUse) {
      return []
    }""", """    if TyperExperiments.absmodel && !u.isVariable && !mayDerive(u, in: scopeOfUse) {
      if TyperCounters.enabled {
        TyperCounters.bump("absmodel.refutedEnvGivens", by: environment.givens.count)
      }
      return []
    }""")
# F. solver rounds
edit("Typer/Solver.swift", """    var selected: (index: Int, survivors: [NameResolutionCandidate])? = nil
""", """    var selected: (index: Int, survivors: [NameResolutionCandidate])? = nil
    TyperCounters.bump("solver.rounds")
    if parked.count == 1 {
      TyperCounters.bump("solver.roundsSingle")
      TyperCounters.bump("solver.probesSingle", by: (goals[parked[0]] as! OverloadConstraint).candidates.count)
    }
""")
edit("Typer/Solver.swift", """      if survivors.count == 1 {
        selected = (i, survivors)""", """      if survivors.count == 1 {
        if survivors.count < k.candidates.count { TyperCounters.bump("solver.commitsPruned") }
        if k.candidates.count == 1 { TyperCounters.bump("solver.singletonSets") }
        selected = (i, survivors)""")
print("ok")
