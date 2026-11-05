root = "/home/hylo/hylo-tc/research/ideas/redundancy/hylo/Sources/FrontEnd/"
def edit(path, old, new, count=1):
    p = root + path; s = open(p).read()
    assert s.count(old) == count, (path, old[:60], s.count(old))
    s = s.replace(old, new); open(p, "w").write(s)
edit("Typer/Typer.swift", """    let u = program.types.reify(t, applying: environment.substitutions, withVariables: .kept)
    return gs.enumerated().reduce(into: []) { (result, grouping) in""", """    let u = program.types.reify(t, applying: environment.substitutions, withVariables: .kept)
    if TyperCounters.enabled {
      TyperCounters.bump("scan.subgoals")
      TyperCounters.bump("scan.threads", by: gs.reduce(0, { $0 + $1.count }))
      if !declarationsOnStack.isEmpty {
        TyperCounters.bump("scan.subgoalsOnStack")
        TyperCounters.bump("scan.threadsOnStack", by: gs.reduce(0, { $0 + $1.count }))
      }
    }
    return gs.enumerated().reduce(into: []) { (result, grouping) in""")
edit("Typer/Typer.swift", """    // Built-in givens only conclude equalities.
    if k == nil {""", """    TyperCounters.bump("index.subgoals")
    TyperCounters.bump("index.threads", by: result.count)
    // Built-in givens only conclude equalities.
    if k == nil {""")
edit("Typer/Typer.swift", """      if wildcards.isEmpty { return xs }
      if xs.isEmpty { return wildcards }
""", """      if wildcards.isEmpty { return xs }
      if xs.isEmpty { return wildcards }
      TyperCounters.bump("index.sorts")
      TyperCounters.bump("index.sortedLen", by: xs.count + wildcards.count)
""")
print("ok")
