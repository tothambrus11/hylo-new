p='/home/hylo/hylo-tc/hylo-new/Sources/FrontEnd/Typer/Typer.swift'
s=open(p).read()
def rep(old,new):
    global s
    assert old in s, old[:80]
    s=s.replace(old,new,1)

rep('''    /// The cache of `Typer.applies(_:to:in:)`.''','''    /// The cache of `Typer.givenIndex(visibleFrom:)`.
    fileprivate var scopeToGivenIndex: [ScopeIdentity: GivenIndex] = [:]

    /// The cache of `Typer.abstractModel(visibleFrom:)`.
    fileprivate var scopeToAbstractModel: [ScopeIdentity: AbstractResolutionModel] = [:]

    /// The cache of `Typer.applies(_:to:in:)`.''')

rep('''    var gs: [[Given]] = []

    // Assumed givens.
    gs.append(contentsOf: environment.givens.reversed().map({ (g) in [g] }))''','''    if TyperExperiments.index || TyperExperiments.absmodel,
      let r = indexedSummon(
        t, in: scopeOfUse, where: environment, then: continuation, penalties: penalties)
    {
      return r
    }

    var gs: [[Given]] = []

    // Assumed givens.
    gs.append(contentsOf: environment.givens.reversed().map({ (g) in [g] }))''')

rep('''    // Check if there are givens in scope that could be used to derive a coercion.
    var result: UInt8 = 0
    for g in chain(environment.givens, givens(visibleFrom: scopeOfUse).joined())  {''','''    // Check if there are givens in scope that could be used to derive a coercion.
    var result: UInt8 = 0
    let sources: [Given]
    if TyperExperiments.index, let ix = givenIndex(visibleFrom: scopeOfUse) {
      sources = ix.coercionSources
    } else {
      sources = Array(givens(visibleFrom: scopeOfUse).joined())
    }
    for g in chain(environment.givens, sources)  {''')

rep('''  /// Returns the givens whose definitions are at the top-level of `m`.
  private mutating func givens(atTopLevelOf m: Module.ID) -> [Given] {''', open('/home/hylo/hylo-tc/research/scripts/index_impl.swift.txt').read() + '''
  /// Returns the givens whose definitions are at the top-level of `m`.
  private mutating func givens(atTopLevelOf m: Module.ID) -> [Given] {''')
open(p,'w').write(s)
