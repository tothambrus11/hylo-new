export const meta = {
  name: 'tc-soundness-review',
  description: 'Review each type-checker optimization for soundness and each report claim; adversarially verify findings',
  phases: [
    { title: 'Review', detail: 'one reviewer per technique + one for report claims' },
    { title: 'Verify', detail: 'independent skeptic per finding tries to refute it' },
  ],
}

// Parameters (pass via Workflow args): repo = absolute path of the hylo-new checkout,
// binid = id printed by `python3 research/exp/tcx.py freeze`, perf = path of perf.
const REPO = (args && args.repo) || '/home/hylo/hylo-tc/hylo-new'
const RES = REPO + '/research'
const BINID = (args && args.binid) || 'REPLACE_WITH_FROZEN_BINARY_ID'
const PERF = (args && args.perf) || 'perf'

const COMMON = `
You are reviewing research optimizations to the Hylo compiler's type checker (Swift).
Repo: ${REPO} (git branch with all experiments committed; see the full change with \`git -C ${REPO} diff origin/main -- Sources\`; per-flag branches: origin/tc/names, tc/unify, tc/solver, tc/resolution, all stacked on tc/infra).
Write-up with all claims: ${RES}/REPORT.md. Original question: ${RES}/intro.md (not committed: ask the user for it; summary in ${RES}/HANDOFF.md). Literature notes: ${RES}/lit-resolution.md, lit-solver-names.md, papers in research/papers/md/.
Each optimization is behind a runtime flag: env HYLO_TC_EXPERIMENTS=comma,list from {names,unify,index,absmodel,solver,loopcheck}; HYLO_TC_ABSDEPTH=2 is the depth used for absmodel. Flag definitions: Sources/FrontEnd/Typer/TyperCounters.swift.
Main changed files: Sources/FrontEnd/Typer/Typer.swift, Solver.swift, AbstractResolution.swift, Sources/FrontEnd/Types/TypeStore.swift.

DEFINITION OF SOUND: an optimization is sound iff, for every program, the type checker produces exactly the same elaboration (types of all syntax trees, name→declaration bindings including implicit/witness arguments, witness tables) and the same diagnostics as with the flag off (or differs only where the baseline is itself broken, e.g. a crash or depth-cap; such cases must be called out explicitly). Resolution must stay deterministic and pick the same (smallest/highest-priority) proof term.

ORACLE (use it!): a frozen release binary with a semantic-dump mode. To test a program under configurations against the baseline:
  cd ${RES}/exp && python3 tcx.py semtest --bin ${BINID} --jobs 2 --env '{"HYLO_TC_ABSDEPTH":"2"}' --configs "index;names,index" --files /path/to/a.hylo /path/to/b.hylo
It prints per config "N/M identical" and a unified diff of the dump for mismatches (exit 1 on any mismatch). Lines look like "file:node : Type", "file:node -> Declaration", "file:node witness...", "diag ...". To inspect raw output: ${RES}/exp/bin/${BINID}/tc-bench --quiet --dump OUT.txt prog.hylo (the stdlib is typed first, then the user file; prefix the command with HYLO_TC_EXPERIMENTS=... to enable flags).
Already established: the 'names' review is done (see ${RES}/review/RESULTS-partial.md: names diverges on programs with cyclic extendee dependencies because skipping applies() changes evaluation order). On all 192 single-file tests in Tests/CompilerTests/{positive,negative} plus research/workloads/*.hylo, every flag alone is dump-identical EXCEPT solver (and configs containing it), which differs on positive/overload-priority.hylo: node 0:75 (the call a.f() in 'let z = a.f() as A<Void>') is typed 'X' in the baseline but 'A<Void>' with solver (X is an associated-type alias = A<Void>).
Hylo syntax: see Tests/CompilerTests/positive/*.hylo for many examples (traits, given/conformances, implicit parameters, extensions, overloading, coercions, generics); research/scripts/gen.py generates stress workloads. Note "fun f(x: T)" means an unlabeled parameter in this version.

PREVIOUS ATTEMPT: an earlier run of this review was interrupted by machine crashes before reporting. Files it left (test programs, oracle outputs) may already be in ${RES}/review/<your-topic>/ — read them first and reuse them (their absolute paths mention /home/hylo/hylo-tc; the same files are now under ${RES}). Do not trust any conclusion they contain without re-running it.
MACHINE: 4 cores, 15 GB RAM, shared with other reviewers. perf is NOT installed; use the profiles in ${RES}/profile/*.txt.

RULES: The working tree is shared with other reviewers. Do NOT edit anything under ${REPO} and do NOT run swift build/test there. Put every file you create under ${RES}/review/<your-topic>/ . Keep --jobs at 2 or below. Never compile the compiler anywhere (no swift build, no repo copies): parallel builds by several agents exhausted memory and crashed the machine. The frozen tc-bench wrapper caps memory at 2.5 GB. Do not attempt precise timing measurements (a controlled benchmark runs separately); rough counters via 'tc-bench --count' are fine.

METHOD: (1) Read the implementation of your technique carefully, line by line, and the REPORT.md section about it. (2) State the soundness argument precisely and look for every way it can break: ordering/penalties/tie-breaking changes, missed candidates, cache keys that are too coarse, scope/visibility differences, generic/existential/associated types, coercions and equality, implicit parameters, recursion, extensions with where-clauses, conditional conformances, aliases, tuples, metatypes, error recovery paths, incrementality/memo invalidation, mutation-order hazards in Swift (e.g. reading program.types before a mutating call). (3) Try hard to construct counterexample Hylo programs and run them through the oracle; a confirmed counterexample is worth far more than a hypothesis. Write at least 8 targeted test programs. (4) Also note where the technique is redundant with another one (overlapping benefit) or adds overhead that might not pay off, and any performance bug (e.g. index fallback taken too often, cache never hit). (5) Report.
Every finding needs concrete evidence: a repro file path + oracle output, or exact code lines and a precise argument. Say 'no issue found' for areas you checked and found sound — list them in checked_ok.`

const TOPICS = [
  { key: 'names', focus: `Technique "names": in Typer.resolve(_:declaredIn:applyingTo:in:statically:) extensions are skipped when declarations(lexicallyIn: extension)[identifier] == nil before checking applies(). Questions: can a member be found through an extension without being lexically declared in it (e.g. nested extensions, conformance declarations inside an extension, synthesized members, operators, labels/argument-label-qualified names, initializers 'init', subscripts, associated types, memberwise init, 'Self'), and does skipping change diagnostics (e.g. "ambiguous" or "not found" notes that enumerate candidates) or side effects of applies() (memoization, caches warmed, diagnostics emitted during applies) that later code depends on?` },
  { key: 'unify', focus: `Technique "unify": TypeStore.unifiableSameShape dispatches on ObjectIdentifier(type(of:)) before casting. Check it is exactly equivalent to the original unifiable() for every type kind (including type variables, aliases, generic parameters, existentials, remote/bundle types, arrows with effects, tuple labels, metatypes, type applications, equality witnesses, error type) and every substitution side effect order. Any case where the original code unifies two different-shaped types (e.g. alias vs aliasee, variable vs anything) must still go through the original path.` },
  { key: 'index', focus: `Technique "index": GivenIndex (byHead / wildcards / coercionSources / groupCount) used by indexedSummon() from summon(...where:) and canDeriveCoercions. Check: penalties (lexical group offsets) are preserved exactly so the same proof term wins; nominalHead() is correct for every head form (aliases that expand to another head, associated types, generic parameters / bare variables as heads, existential types, metatypes, tuples, type applications, conditional givens with where-clauses, givens that are functions/implicit parameters); the fallback conditions (coercionSources non-empty, pending assumed equality) are sufficient; memoization by scope (scopeToGivenIndex) is valid at all points (givens added later, declarationsOnStack, local givens inside function bodies, assumed givens during resolution, extension-local givens); builtins are only included when the head is nil — is that right?` },
  { key: 'absmodel', focus: `Technique "absmodel": AbstractResolution.swift + abstractModel(visibleFrom:)/abstractClause(of:)/mayDerive in Typer.swift. It is a depth-k (k=HYLO_TC_ABSDEPTH, default 3, experiments use 2) abstract least model (Sato-Tamaki depth abstraction) used to refute resolution goals before search. Soundness requires: the abstract model over-approximates every derivable goal (every concrete derivation maps to an abstract derivation), truncation to ⊤ is monotone, unify with ⊤ treats ⊤ as matching anything, no occurs check is safe, premises with a context are dropped (over-approximation OK), clauses whose head is ⊤/variable/equality make the model inconclusive, equality goals are never refuted, coercion derivations / built-in givens / implicit-parameter assumptions / givens assumed during resolution / pending premises (assumed givens) / sibling candidates are all accounted for, the incremental parent-scope model plus per-module sharing at file scope is valid, factLimit overflow is handled conservatively, and subsumption in insert() never drops a needed fact. Also check abstraction(of:) of every type kind (associated types, existentials, metatypes, arrows, remote, bundles → must be ⊤ unless provably safe). Try programs with conditional conformances, recursive instances, tuples, generic givens, given functions with implicit params, and goals that are only derivable through coercion.` },
  { key: 'solver', focus: `Technique "solver": Solver.swift parks OverloadConstraint goals while deferring, then resolveParked() probes each choice in a forked solver (probe mode returns at quiescence), keeps zero-error survivors (or all if none), commits a sole survivor in place (equality subgoal + binding), else branches with solve(overload:among:) on the most constrained set. Check soundness vs the baseline branching (which explores all choices and ranks solutions): can a choice with errors at quiescence in a probe still be part of the best solution of the baseline (e.g. errors that later constraints would fix, or ranking/penalty/'better' comparisons between solutions that prefer a choice the probe discarded, overload priority via expected type, members inherited by extension vs by conformance)? Is committing in place equivalent to the baseline's choice (scores, bindings recorded in the solution, the order of substitutions)? Explain and characterize the known mismatch on Tests/CompilerTests/positive/overload-priority.hylo (node 0:75 typed 'X' vs 'A<Void>'): is it a harmless sugar difference or a real semantic change, what exact code path causes it, and how to fix it so the dump is identical. Look for more mismatches with programs mixing overloads, literals, expected types, closures, coercions and generic functions.` },
  { key: 'loopcheck', focus: `Technique "loopcheck": Environment.ancestry, formThread(..., ancestors:), summon(...ancestors:) prunes a subgoal whose reified type equals a reified ancestor; threadContinuation passes e.ancestry.removeValue(forKey:). Check: pruning an identical-ancestor subgoal is complete for SLD with the given selection (Bol-Apt-Klop "equality check" is sound for pure Horn clauses without side effects, but Hylo resolution has assumed givens/pending premises, sibling candidates, coercions, and a BFS with depth cap and penalties — can pruning remove the derivation that the baseline returns, or change which result wins, or change depth-exhausted diagnostics?). Are ancestors tracked per thread correctly when threads fork, when continuations are resumed, and across assumed givens? Is the comparison on reified types (with type variables) correct when variables are later bound?` },
  { key: 'claims', focus: `The REPORT.md as a whole: check every quantitative and qualitative claim against the data and code in ${RES} (diff/, workloads/, scripts/, lit files, papers/md). In particular: (a) the answer given to intro.md (depth-2 abstract least model is a sound cheap 'resolution will fail' check; loopcheck; what it can/cannot refute; is the cost claim plausible?) — is the theory correct and correctly attributed to the literature (Dowling-Gallier, Knuth 1977 superior functions, Sato-Tamaki, Bol-Apt-Klop, Frühwirth et al., Heintze-Jaffar, Gallagher-Puebla, Lean 4 tabled resolution, GHC RoughMap, scope graphs/Néron/Zwaan, Swift constraint graph/Freuder)? Check the papers' md files for misattributions. (b) the depth-cap finding: chain9 (research/workloads/chain9.hylo) is rejected although a finite derivation exists — reproduce with the frozen binary and confirm it is the depth cap (maxImplicitDepth = 10) and not something else. (c) the pre-existing crash in negative/illegal-enum-case.hylo — reproduce with baseline. (d) statements of soundness for each technique: are they stated with correct preconditions? (e) recommendations: are they justified by the numbers? Flag overstated or unsupported claims, wrong numbers, wrong citations.` },
]

const FINDINGS = {
  type: 'object',
  properties: {
    soundness_argument: { type: 'string', description: 'precise statement of why the technique is (or is not) sound, with preconditions' },
    verdict: { type: 'string', enum: ['sound', 'sound-with-caveats', 'unsound', 'unclear'] },
    findings: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      title: { type: 'string' },
      severity: { type: 'string', enum: ['critical', 'major', 'minor', 'info'] },
      kind: { type: 'string', enum: ['unsound', 'perf', 'redundancy', 'claim', 'code-quality', 'baseline-bug'] },
      evidence: { type: 'string', description: 'repro file path + oracle output excerpt, or exact code lines + argument' },
      repro_files: { type: 'array', items: { type: 'string' } },
      suggested_fix: { type: 'string' },
    }, required: ['id', 'title', 'severity', 'kind', 'evidence', 'suggested_fix'] } },
    checked_ok: { type: 'array', items: { type: 'string' } },
    tests_written: { type: 'array', items: { type: 'string' } },
    redundancy_notes: { type: 'string' },
  },
  required: ['soundness_argument', 'verdict', 'findings', 'checked_ok', 'tests_written', 'redundancy_notes'],
}

const VERDICT = {
  type: 'object',
  properties: {
    confirmed: { type: 'boolean' },
    severity: { type: 'string', enum: ['critical', 'major', 'minor', 'info'] },
    reasoning: { type: 'string' },
    reproduced: { type: 'boolean', description: 'true iff you re-ran a repro and observed the claimed behavior' },
    fix: { type: 'string', description: 'the fix you recommend (may differ from the suggested one), concrete enough to implement' },
  },
  required: ['confirmed', 'severity', 'reasoning', 'reproduced', 'fix'],
}

const MAXV = (args && args.maxVerify) || 3  // verifiers per topic (most severe first)
const ONLY = args && args.topics  // e.g. ['unify','index','absmodel','solver','loopcheck','claims']
const results = await pipeline(
  ONLY ? TOPICS.filter(t => ONLY.includes(t.key)) : TOPICS,
  t => agent(`${COMMON}\n\nYOUR TOPIC (${t.key}):\n${t.focus}\nYour scratch directory: ${RES}/review/${t.key}/`,
    { label: `review:${t.key}`, phase: 'Review', schema: FINDINGS }),
  (rev, t) => {
    if (!rev) return null
    const rank = { critical: 0, major: 1, minor: 2 }
    const toVerify = rev.findings.filter(f => f.severity !== 'info').sort((a, b) => rank[a.severity] - rank[b.severity]).slice(0, MAXV)
    return parallel(toVerify.map(f => () => agent(`${COMMON}\n\nYou are an independent skeptic. Another reviewer (topic ${t.key}) reported the finding below. Try to REFUTE it: re-run any repro with the oracle, read the cited code yourself, and check whether the claimed behavior really differs from the baseline or the claim is really wrong. If uncertain, say confirmed=false. Also propose the best concrete fix. Scratch dir: ${RES}/review/${t.key}/verify-${f.id}/\n\nFINDING:\n${JSON.stringify(f, null, 1)}`,
      { label: `verify:${t.key}:${f.id}`, phase: 'Verify', schema: VERDICT }).then(v => ({ ...f, verdict: v }))))
      .then(vs => ({ topic: t.key, verdict: rev.verdict, soundness_argument: rev.soundness_argument, checked_ok: rev.checked_ok, tests_written: rev.tests_written, redundancy_notes: rev.redundancy_notes, info: rev.findings.filter(f => f.severity === 'info' || !toVerify.includes(f)), verified: vs.filter(Boolean) }))
  },
)
return results.filter(Boolean)
