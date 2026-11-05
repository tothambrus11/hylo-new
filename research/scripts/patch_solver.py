p='/home/hylo/hylo-tc/hylo-new/Sources/FrontEnd/Typer/Solver.swift'
s=open(p).read()
def rep(old,new):
    global s
    assert old in s, old[:90]
    s=s.replace(old,new,1)
rep('''  /// The number of root goals.
  private let rootCount: Int''','''  /// The number of root goals.
  private let rootCount: Int

  /// Experiment: overload constraints whose resolution is deferred until other goals settle.
  private var parked: [GoalIdentity] = []

  /// Experiment: `true` iff this solver is probing the consequences of a single choice.
  private var probing: Bool = false

  /// Experiment: `true` iff a probe has run to quiescence.
  private var probeFinished: Bool = false''')
rep('''    while let g = fresh.popLast() {
      TyperCounters.bump("solver.goalSteps")''','''    let deferring = TyperExperiments.solver
    while true {
      guard let g = fresh.popLast() else {
        if !deferring { break }
        if probing {
          probeFinished = true
          return nil
        }
        if !parked.isEmpty {
          switch resolveParked() {
          case .running: continue
          case .canceled: return nil
          case .terminated(let r): return r
          }
        }
        refreshCoercionAndWideningConstraints()
        if fresh.isEmpty { break } else { continue }
      }
      TyperCounters.bump("solver.goalSteps")''')
rep('''        case is OverloadConstraint:
          return me.solve(overload: g).map(SolverStatus.terminated(_:)) ?? .canceled''','''        case is OverloadConstraint:
          if deferring {
            me.parked.append(g)
            return .running
          }
          return me.solve(overload: g).map(SolverStatus.terminated(_:)) ?? .canceled''')
rep('''      switch status {
      case .running:
        if fresh.isEmpty { refreshCoercionAndWideningConstraints() }''','''      switch status {
      case .running:
        if fresh.isEmpty && !deferring { refreshCoercionAndWideningConstraints() }''')
rep('''  /// Discharges `g`, which is an overload constraint.
  private mutating func solve(overload g: GoalIdentity) -> Solution? {
    let k = goals[g] as! OverloadConstraint

    var viable: [(choice: NameResolutionCandidate, solution: Solution)] = []
    for choice in k.candidates {''', open('/home/hylo/hylo-tc/research/scripts/solver_impl.swift.txt').read())
open(p,'w').write(s)
p='/home/hylo/hylo-tc/hylo-new/Sources/FrontEnd/Typer/TyperCounters.swift'
s=open(p).read()
if 'static var solver' not in s:
    s=s.replace('''  /// Refute queries using''','''  /// Defer overload branching and prune choices by forward checking.
  nonisolated(unsafe) public static var solver: Bool = enabled.contains("solver")

  /// Refute queries using''')
open(p,'w').write(s)
