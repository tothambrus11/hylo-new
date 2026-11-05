import re
p='/home/hylo/hylo-tc/hylo-new/Sources/FrontEnd/Typer/Typer.swift'
s=open(p).read()
def rep(old,new,count=1):
    global s
    assert s.count(old) >= count, (s.count(old), old[:90])
    s=s.replace(old,new,count)

# Environment: ancestry of assumed givens.
rep('''      /// The identifier of the next assumed given.
      let nextGivenIdentifier: Int
''','''      /// The identifier of the next assumed given.
      let nextGivenIdentifier: Int

      /// Experiment: for each assumed given introduced as the premise of a given, the goals of
      /// which the premise is a (transitive) subgoal.
      var ancestry: [Int: [AnyTypeIdentity]] = [:]
''')
rep('''        let e = Environment(
          substitutions: substitutions, givens: givens + gs,
          nextGivenIdentifier: nextGivenIdentifier + gs.count)
        return e''','''        var e = Environment(
          substitutions: substitutions, givens: givens + gs,
          nextGivenIdentifier: nextGivenIdentifier + gs.count)
        e.ancestry = ancestry
        return e''')
rep('''        let e = Environment(
          substitutions: substitutions, givens: givens.appending(g), nextGivenIdentifier: i + 1)''','''        var e = Environment(
          substitutions: substitutions, givens: givens.appending(g), nextGivenIdentifier: i + 1)
        e.ancestry = ancestry''')
# threadContinuation
rep('''    if case .assumed(let i, let assumed) = thread.environment.givens.last {
      let e = ResolutionThread.Environment(
        substitutions: operand.substitutions, givens: thread.environment.givens.dropLast(),
        nextGivenIdentifier: thread.environment.nextGivenIdentifier)
      var t = thread.tail
      t.append(.init(i, in: operand))
      return .next(
        summon(assumed, in: scopeOfUse, where: e, then: t, penalties: operand.penalties))''','''    if case .assumed(let i, let assumed) = thread.environment.givens.last {
      var e = ResolutionThread.Environment(
        substitutions: operand.substitutions, givens: thread.environment.givens.dropLast(),
        nextGivenIdentifier: thread.environment.nextGivenIdentifier)
      e.ancestry = thread.environment.ancestry
      let ancestors = e.ancestry.removeValue(forKey: i) ?? []
      var t = thread.tail
      t.append(.init(i, in: operand))
      return .next(
        summon(
          assumed, in: scopeOfUse, where: e, then: t, penalties: operand.penalties,
          ancestors: ancestors))''')
# summon(where:) signature + loop check
rep('''    then continuation: [ResolutionThread.ContinuationItem],
    penalties: Int
  ) -> [ResolutionThread] {
    TyperCounters.bump("summon.subgoals")''','''    then continuation: [ResolutionThread.ContinuationItem],
    penalties: Int,
    ancestors: [AnyTypeIdentity] = []
  ) -> [ResolutionThread] {
    TyperCounters.bump("summon.subgoals")

    // Experiment: a subgoal identical to one of its ancestors can't be part of a smallest
    // derivation, since the derivation of the ancestor could be replaced by that of the subgoal.
    if TyperExperiments.loopcheck && !ancestors.isEmpty {
      let u = program.types.reify(t, applying: environment.substitutions, withVariables: .kept)
      for a in ancestors {
        let b = program.types.reify(a, applying: environment.substitutions, withVariables: .kept)
        if b == u {
          TyperCounters.bump("loopcheck.pruned")
          return []
        }
      }
    }''')
rep('''      let r = indexedSummon(
        t, in: scopeOfUse, where: environment, then: continuation, penalties: penalties)''','''      let r = indexedSummon(
        t, in: scopeOfUse, where: environment, then: continuation, penalties: penalties,
        ancestors: ancestors)''')
rep('''        let r = formThread(
          matching: w, to: u, in: environment, then: continuation,
          penalties: penalties + grouping.offset)''','''        let r = formThread(
          matching: w, to: u, in: environment, then: continuation,
          penalties: penalties + grouping.offset, ancestors: ancestors)''')
# formThread
rep('''    then tail: [ResolutionThread.ContinuationItem] = [],
    penalties: Int = 0
  ) -> ResolutionThread {
    var environment = environment''','''    then tail: [ResolutionThread.ContinuationItem] = [],
    penalties: Int = 0,
    ancestors: [AnyTypeIdentity] = []
  ) -> ResolutionThread {
    var environment = environment''')
rep('''        let h = i.usings.first!
        let (e, v) = environment.assuming(given: h)''','''        let h = i.usings.first!
        var (e, v) = environment.assuming(given: h)
        if TyperExperiments.loopcheck {
          e.ancestry[environment.nextGivenIdentifier] = ancestors.appending(queried)
        }''')
# indexedSummon
rep('''    then continuation: [ResolutionThread.ContinuationItem],
    penalties: Int
  ) -> [ResolutionThread]? {''','''    then continuation: [ResolutionThread.ContinuationItem],
    penalties: Int,
    ancestors: [AnyTypeIdentity]
  ) -> [ResolutionThread]? {''')
s=re.sub(r'(result\.append\(formThread\(\n\s+matching: expression\(referringTo: (?:g|e\.given)\), to: u, in: environment, then: continuation,\n\s+penalties: penalties \+ (?:i|a \+ e\.group|a \+ ix\.groupCount))\)\)',
         r'\1, ancestors: ancestors))', s)
assert s.count('ancestors: ancestors))') == 4, s.count('ancestors: ancestors))')
open(p,'w').write(s)

p='/home/hylo/hylo-tc/hylo-new/Sources/FrontEnd/Typer/TyperCounters.swift'
s=open(p).read()
if 'static var loopcheck' not in s:
    s=s.replace('''  /// Refute queries using''','''  /// Prune resolution subgoals identical to one of their ancestors.
  nonisolated(unsafe) public static var loopcheck: Bool = enabled.contains("loopcheck")

  /// Refute queries using''')
open(p,'w').write(s)
