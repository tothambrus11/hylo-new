export const meta = {
  name: 'tc-future-ideas',
  description: 'Brainstorm next-round type-checker speedups from profiles (4 lenses) and rank them with a judge',
  phases: [
    { title: 'Ideate', detail: 'four independent lenses propose ideas' },
    { title: 'Judge', detail: 'dedup, score, pick the implementation slate' },
  ],
}

// Parameters (pass via Workflow args): repo = absolute path of the hylo-new checkout,
// binid = id printed by `python3 research/exp/tcx.py freeze`, perf = path of perf.
const REPO = (args && args.repo) || '/home/hylo/hylo-tc/hylo-new'
const RES = REPO + '/research'
const BINID = (args && args.binid) || 'REPLACE_WITH_FROZEN_BINARY_ID'
const PERF = (args && args.perf) || 'perf'

const CTX = `
Context: research on speeding up the Hylo compiler's type checker (Swift). Repo ${REPO} (uncommitted changes on branch tc-perf-research; diff in ${RES}/tc-experiments.patch). Write-up: ${RES}/REPORT.md. Literature notes: ${RES}/lit-resolution.md, lit-solver-names.md, research/papers/md/.
Six optimizations already exist behind env flags HYLO_TC_EXPERIMENTS=names,unify,index,absmodel,solver,loopcheck (see REPORT.md §5). With all on, stdlib typing went 461 ms → ~160 ms.
FRESH PROFILES with all six flags on (perf, 4 kHz, frame-pointer call graphs, symbolized self% and inclusive%):
  ${RES}/profile/allon.txt (stdlib only, 5 repeats incl. parsing)
  ${RES}/profile/members-big.txt, breadth80.txt, ovl-8-8.txt, ovr-3-10.txt (stress workloads in research/workloads/, generator research/scripts/gen.py)
Notable already: Program.initializeStandardLibraryCaches() ≈14% inclusive of the whole stdlib run (it calls select(from:.symbol(name)) once per StandardLibraryEntity, each scanning all stdlib syntax with 'as? any Annotatable' casts); canDeriveCoercions ≈12.6%; resolve(memberOf:) 30%; swift_dynamicCast 18% inclusive; retain/release ~20% self; TupleCache getOrInsert 3.7% self (runtime tuple metadata instantiation in unspecialized generic code); TypeStore.subscript.getter 8.9%; on members-big, specialized resolve<A>(declaredIn:applyingTo:...) 41% and Dictionary.find 16%; on breadth80, evaluateTypeAscription/declaredType 27% and StableDictionary.assignValue 12%.
A frozen binary for experiments: ${RES}/exp/bin/${BINID}/tc-bench (usage: [HYLO_TC_EXPERIMENTS=..] tc-bench [--count] [--quiet] [--repeat N] [--dump out.txt] file.hylo). You may run perf: ${PERF} record -F 4000 -g -o X.data <cmd>; then python3 ${RES}/scripts/perfsym.py <perf> X.data 60 to symbolize. Put any file you create under ${RES}/ideas/<your-lens>/. Do NOT edit hylo-new, and do NOT compile the compiler ANYWHERE (no copies of the repo, no swift build): parallel builds exhausted the machine's memory and crashed it. Reason from code, counters (--count), profiles and the frozen binary only. If earlier attempts left a copy of the repo under research/ideas/<lens>/hylo, you may read it but delete its .build directory.
Hard constraint for every idea: it must be SOUND = produce exactly the same elaboration (types, bindings, witnesses) and diagnostics as the baseline on every program, and be implementable behind a new runtime flag in TyperExperiments, independently of the other flags (it may assume nothing about which other flags are on). An idea that changes semantics (e.g. removing the resolution depth cap) is allowed only if clearly labeled 'semantic change' and kept separate.
Read the relevant code before proposing; each idea must cite the exact functions/lines it changes and the profile evidence (which % it attacks), estimate the gain on stdlib and on the stress workloads, and explain the soundness argument and the risk. Also tell which existing flags it overlaps with (redundancy) — we want to find out whether some existing flags become unnecessary.`

const LENSES = [
  { key: 'constant-factors', prompt: 'LENS: Swift constant factors seen in the profile — existential casts (swift_dynamicCast, conformsToProtocol), generic metadata instantiation (getGenericMetadata, TupleCache), retain/release traffic, Hasher, String comparisons, StableDictionary/StableSet access patterns, copy-on-write of large structs (e.g. program.types, Environment), unspecialized generics. Find the top call sites responsible (use perf yourself on the frozen binary with deeper analysis if useful) and propose targeted fixes (tag dispatch, @inline/@_specialize, borrowing instead of copying, interning strings, caching casts).' },
  { key: 'caching', prompt: 'LENS: caching, memoization, indexing and incrementality — what is recomputed many times with the same inputs? E.g. initializeStandardLibraryCaches symbol lookup, member lookup results per (type, name, scope), canDeriveCoercion results, declaredType, extension applicability per (extension, type), declarations(lexicallyIn:) tables, summon results across scopes (with correct invalidation keys: visible givens, assumed givens, pending premises). Use counters (tc-bench --count) and code reading to quantify hit rates before proposing.' },
  { key: 'algorithms', prompt: 'LENS: algorithmic / graph-theoretic improvements grounded in the literature (see lit files and papers): e.g. tabled/memoized resolution with size-ordered (Knuth 1977 superior-function / A*LD) search that would remove the depth cap; semi-naive and incremental Datalog for abstract models; scope-graph query specialization for name lookup; constraint-graph connected components and most-constrained-variable ordering in the solver; discrimination trees beyond head symbols; union-find for type variables. For each, explain precisely how it maps onto the Hylo code and why it is sound (or label as semantic change).' },
  { key: 'redundancy', prompt: 'LENS: interaction and redundancy analysis of the six existing flags plus overhead — for each existing flag, measure with counters (tc-bench --count, HYLO_TC_EXPERIMENTS subsets) how much work it removes when the others are already on (e.g. does absmodel still refute anything once index+loopcheck are on? does unify still matter once names+index have cut the number of unifications? is loopcheck subsumed by absmodel?). Use counter values, not timings (the machine is shared). Then propose simplifications (removing/merging flags) and cheap fixes to reduce overhead of each flag (e.g. the abstract model build cost, the ancestry bookkeeping in loopcheck, probing cost in solver).' },
]

const IDEAS = {
  type: 'object',
  properties: {
    ideas: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string', description: 'short flag-style name, lowercase, e.g. symcache' },
      summary: { type: 'string' },
      code_locations: { type: 'string' },
      profile_evidence: { type: 'string' },
      expected_gain: { type: 'string' },
      soundness: { type: 'string' },
      semantic_change: { type: 'boolean' },
      overlaps_with: { type: 'string' },
      implementation_sketch: { type: 'string' },
      effort: { type: 'string', enum: ['S', 'M', 'L'] },
      risk: { type: 'string', enum: ['low', 'medium', 'high'] },
    }, required: ['name', 'summary', 'code_locations', 'profile_evidence', 'expected_gain', 'soundness', 'semantic_change', 'overlaps_with', 'implementation_sketch', 'effort', 'risk'] } },
    measurements: { type: 'string', description: 'any counters/profiles you gathered, with file paths' },
  },
  required: ['ideas', 'measurements'],
}

phase('Ideate')
const all = await parallel(LENSES.map(l => () => agent(`${CTX}\n\n${l.prompt}\nPropose 3–6 ideas, best first.`, { label: `ideate:${l.key}`, phase: 'Ideate', schema: IDEAS })))
const ideas = all.filter(Boolean).flatMap((r, i) => r.ideas.map(x => ({ ...x, lens: LENSES[i].key })))
const measurements = all.filter(Boolean).map((r, i) => `[${LENSES[i].key}] ${r.measurements}`).join('\n\n')
log(`${ideas.length} ideas proposed`)

phase('Judge')
const SLATE = {
  type: 'object',
  properties: {
    slate: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, merged_from: { type: 'array', items: { type: 'string' } },
      rationale: { type: 'string' }, spec: { type: 'string', description: 'complete implementation brief for an engineer: files, functions, data structures, flag name, soundness argument, how to test' },
      expected_gain: { type: 'string' }, semantic_change: { type: 'boolean' }, priority: { type: 'integer' },
    }, required: ['name', 'merged_from', 'rationale', 'spec', 'expected_gain', 'semantic_change', 'priority'] } },
    rejected: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, reason: { type: 'string' } }, required: ['name', 'reason'] } },
    redundancy_hypotheses: { type: 'string', description: 'testable hypotheses about which existing flags are redundant given others, to be checked by the factorial experiment' },
  },
  required: ['slate', 'rejected', 'redundancy_hypotheses'],
}
const verdict = await agent(`${CTX}\n\nYou are the judge. Below are ideas from four independent lenses plus their measurements. Deduplicate and merge overlapping ideas, check the key claims against the code yourself (spot-check at least the top candidates' code locations and soundness arguments), and select a slate of 5–8 ideas to implement now, each as an independent runtime flag, ranked by expected payoff / (effort × risk). Prefer ideas with large measured profile shares. Include at most one 'semantic change' idea and mark it. Each spec must be complete enough for an engineer who has not seen this conversation.\n\nIDEAS:\n${JSON.stringify(ideas, null, 1)}\n\nMEASUREMENTS:\n${measurements}`, { label: 'judge', phase: 'Judge', schema: SLATE })
return { verdict, ideas }
