"""Builds START-HERE.html, questions/README.md and reproducers/README.md.

usage: python3 make_start_here.py
The verdicts quoted here were observed with the final implementation; `questions/observed.txt`
and `reproducers/observed.txt` hold the raw output."""
import html, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
R = lambda p: open(os.path.join(HERE, p)).read()

def source(path):
    """The program without its header and comment lines, escaped."""
    lines = [l for l in R(path).split("\n") if not l.startswith("//")]
    return html.escape("\n".join(lines).strip("\n"))

def md(s):
    s = re.sub(r"<code>(.*?)</code>", lambda m: "`" + html.unescape(m.group(1)) + "`", s)
    s = re.sub(r"<span class=\"flag\">(.*?)</span>", r"`\1`", s)
    s = re.sub(r"</?(strong|em|a)[^>]*>", "", s)
    return html.unescape(s)

# (id, title, weight, question, [program files], today, assumed, otherwise)
GROUPS = [
 ("Conformances and equalities", [
  ("1", "Are conformances coherent across equal types?", True,
   "With <code>T == U</code>, <code>T is P</code> and <code>U is P</code>, are the two requirements the same witness, so that <code>T.X</code> and <code>U.X</code> are the same type?",
   ["q01-coherence.hylo"],
   "Rejected, by the existing implementation and by the fixes. This is the compiler's negative test <code>associated-type-inequality</code>.",
   "No: two requirements are two witnesses, which may define <code>X</code> differently. Every fix follows this reading.",
   "If conformances are coherent, problem 7 below is not a defect, types can be rewritten to a representative of their equality class (rejected here as unsafe, because a conformance is selected by the way a type is written), and the restrictions of <span class=\"flag\">abstractstrict</span> can be lifted."),
  ("2", "Inside a trait, is <code>Self.X</code> equal to <code>T.X</code> when <code>T == Self</code> and <code>T is P</code>?", True,
   "<code>T is P</code> is a second requirement, which the caller satisfies independently of the witness that the trait stands for.",
   ["q02a-self-projection.hylo", "q02b-self-projection-conversion.hylo"],
   "<code>q02a</code>: accepted by the existing implementation, rejected by the fixes. <code>q02b</code> uses the rule to convert a <code>W.X</code> into a <code>V.X</code> under the where clause of question 1: the existing implementation exhausts memory on it; with the equality procedure alone it is accepted; with the fix it is rejected.",
   "No, for consistency with question 1: a selection through the trait's own witness equals only a selection through that same witness (<span class=\"flag\">abstractstrict</span>). Eight test programs of the shape of <code>q02a</code> are rejected as a result.",
   "If they are equal, the rule must be reconciled with question 1, since <code>q02b</code> performs exactly the conversion that the negative test forbids."),
  ("3", "What do equalities between concrete types mean?", False,
   "Does <code>Box&lt;T&gt; == Box&lt;U&gt;</code> give <code>T == U</code>? Is <code>where T == A, T == B</code>, for two distinct structs, an error where it is declared?",
   ["q03a-injectivity.hylo", "q03b-two-concrete-types.hylo"],
   "<code>q03a</code> is rejected: type constructors are not injective for equalities. <code>q03b</code> is accepted: in the body, an <code>A</code> is passed where a <code>B</code> is expected. No caller can satisfy the clause. Both behaviours are those of the existing implementation and are unchanged.",
   "Nothing is assumed; the equality procedure reproduces both behaviours.",
   "Injectivity would be a new rule of the congruence closure. Rejecting <code>q03b</code> at the declaration would be a new check for clauses that equate two distinct nominal types."),
  ("4", "Are the members of <code>A</code> available on a <code>T</code> when <code>T == A</code>?", False,
   "Members of a trait are found through an equality; members of a struct, and its extensions, are not.",
   ["q04a-struct-member-through-equality.hylo", "q04b-trait-member-through-equality.hylo"],
   "<code>q04a</code> is rejected (\"type 'T' has no member 'foo'\"), <code>q04b</code> is accepted. Unchanged.",
   "Nothing is assumed.",
   "If struct members should be found, member lookup has to consult the equalities in scope."),
  ("5", "How should a trait state an equality between its associated types?", False,
   "Swift's <code>Sequence</code> has <code>Iterator.Element == Element</code>. In a survey of the Swift standard library, swift-collections and Rust's iterator library, 6% to 24% of the functions have an equality in scope, mostly through traits.",
   ["q05-equality-in-trait.hylo"],
   "A syntax error: \"expected 'is'\".",
   "Nothing is assumed; the feature does not exist.",
   "An equality stated by a trait holds for every conforming type, so it is not ground. Two of the techniques (<span class=\"flag\">eqindex</span>, <span class=\"flag\">coeset</span>) rely on the equalities in scope being ground; they fall back to the general path otherwise and would need to be revisited."),
  ("6", "Does anything depend on the shape of an equality proof?", False,
   "The decision procedure builds the term of an equality proof differently from the search. On the compiler's tests, this is the only difference in the elaborated output (two files).",
   [],
   "No program: the question is about later phases.",
   "No: any proof term of the right type is as good as another.",
   "If lowering, or a checker of derivations, needs a particular form, the procedure must build that form."),
 ]),
 ("Requirements of a where clause", [
  ("7", "Is the order of requirements meant to be significant?", False,
   "A requirement is an assumption for the requirements written after it, so reordering a clause changes how many steps a call needs.",
   ["q07a-where-order.hylo", "q07b-where-order-swapped.hylo"],
   "<code>q07a</code> is accepted (8 steps); <code>q07b</code>, the same program with the two requirements swapped, is rejected (12 steps, past the bound of question 11). Unchanged.",
   "The existing rule is kept.",
   "If the order should not matter, the requirements must be assumptions for each other in both directions, or in neither. The experiment <span class=\"flag\">heightbound</span> accepts both programs by changing the bound instead."),
  ("8", "Which witness does a requirement get when another requirement mentions it?", True,
   "For <code>where T is P, T.X is Q</code>: is the witness of <code>T is P</code> the one that resolving it alone gives, or may the second requirement select among the conformances in scope?",
   ["q08-which-witness.hylo"],
   "Rejected by both. The existing implementation rejects every call whose requirements mention an associated type of another requirement. The fix rejects this one because <code>A is P</code> alone resolves to the local conformance, for which <code>A.X</code> is <code>C</code>, and <code>C</code> is not <code>Q</code>.",
   "On its own: the requirement is resolved first, a tie is an ambiguity, and the dependent requirement is then proved for that witness (<span class=\"flag\">premcommit</span>).",
   "Solving the requirements together accepts <code>q08</code> through the shadowed conformance of the module. Five programs of the test corpus differ between the two readings."),
  ("9", "Is an associated type selected through a declared conformance equal to its definition?", False,
   "In particular for a generic conformance, where the definition mentions the conformance's own parameters.",
   ["q09a-generic-conformance-unsound.hylo", "q09b-generic-conformance-valid.hylo"],
   "<code>q09a</code> is accepted by the existing implementation: an <code>A</code> is passed where a <code>C</code> is expected. <code>q09b</code>, which is valid, is rejected by it. The fix reverses both.",
   "Yes: <code>A.X</code> through <code>given &lt;T&gt; =&gt; T is P { type X = T }</code> is <code>A</code>, with the arguments and the witnesses of the conformance substituted into the definition (<span class=\"flag\">assocsubst</span>).",
   "Probably uncontroversial. One related case has no diagnostic: a parameter of a conformance that neither its head nor its requirements determine (<code>given &lt;T, U&gt; =&gt; Box&lt;T&gt; is P { type X = U }</code>) yields a fresh type at each use. Should it be an error at the declaration?"),
 ]),
 ("Ranking and the bound on derivations", [
  ("10", "Is the ranking of derivations through equalities intended?", False,
   "Which of two conformances wins depends on the side on which an equality is written, because penalties count pending requirements and a derivation that uses symmetry is longer.",
   ["q10a-ranking.hylo", "q10b-ranking-other-side.hylo"],
   "<code>q10a</code> (<code>B == A, A == C</code>) is accepted; <code>q10b</code> (<code>B == A, C == A</code>) is rejected as ambiguous. Of 800 generated goals with two symmetric derivations, 408 are accepted and 392 reported as ambiguous. Unchanged: the fixes reproduce the ranking exactly.",
   "The ranking is treated as part of the language, and every technique was required to preserve it.",
   "If symmetric derivations should always be ambiguous (or never), the ranking can be defined on the equality classes, and the techniques no longer need to reproduce step counts."),
  ("11", "Is the bound of ten steps part of the language?", True,
   "Does it bound the size of a derivation (all the givens used for a call) or its depth? Do the steps that prove equalities count? Is reaching it an error, or a silent failure after which another extension or overload is selected?",
   ["q11a-bound-four.hylo", "q11b-bound-five.hylo", "q11c-bound-selects-member.hylo"],
   "<code>q11a</code> (9 givens) is accepted. <code>q11b</code> (11 givens, valid) is rejected with \"no coercion\", without mention of the bound. In <code>q11c</code> two extensions apply, and proving so needs nine equalities for the first and eight for the second: the existing implementation exhausts memory; with the equality procedure alone the member of the second extension is called; in the recommended configuration, where equalities proved by the procedure are not counted, the member of the first is.",
   "The bound is kept as it is, on the size of a derivation, with silent failure. Equalities decided by the procedure are not counted (<span class=\"flag\">eqeager</span>), which is the one intended change of behaviour among the performance techniques.",
   "The experiment <span class=\"flag\">heightbound</span> bounds the depth instead and accepts <code>q11b</code> and <code>q07b</code>. If reaching the bound were an error, <code>q11c</code> would have one meaning."),
 ]),
 ("Declaration order", [
  ("12", "May the types of extensions and givens depend on each other?", False,
   "Looking up the type that one extension extends can require the other extension, and conversely.",
   ["q12-mutually-dependent-extensions.hylo"],
   "The existing implementation accepts <code>q12</code> in 12 of the 24 orders of its declarations. The fix accepts it in all 24: it computes these types in rounds until they are stable, and reports the declarations for which no stable reading is found.",
   "Yes, when the iteration reaches a stable reading (<span class=\"flag\">sigrounds</span>).",
   "A stricter rule, rejecting every such dependency, can be added as a check on the stable result. It would also remove the remaining unproved step in the argument that the overload techniques preserve results."),
  ("13", "May a given be a candidate in its own initializer, and what is a given with an inferred type worth outside a function?", False,
   "Today a given is hidden while its own type is computed, and a given without a written type is typed on demand, inside the first resolution that meets it.",
   ["q13a-given-in-own-initializer.hylo", "q13b-given-initialized-with-itself.hylo", "q13c-inferred-given-order.hylo"],
   "<code>q13a</code> is accepted: <code>w</code> is initialized with <code>other</code>. <code>q13b</code> is accepted by every configuration: a given with a written type is the only candidate for its own initializer. <code>q13c</code> is accepted in 15 of the 24 orders of its declarations, by the existing implementation and by the fixes alike.",
   "The fix for declaration order covers declarations whose type is written; <code>q13c</code> is not fixed.",
   "Four options were tried and none is adopted (<code>experiments/inferred-givens/README.md</code>). The simplest is a rule: a given declared outside a function must have a written type. The most complete one makes <code>q13c</code> independent of the order but rejects <code>q13a</code>, because the given then sees itself."),
  ("14", "Is the order of givens in a function body meant to matter, and may a where clause name a declaration of the body it governs?", False,
   "Givens declared in a body are visible in the whole body, before their declaration.",
   ["q14a-givens-in-body.hylo", "q14b-givens-in-body-swapped.hylo", "q14c-where-clause-uses-body.hylo"],
   "The existing implementation rejects <code>q14a</code> and accepts <code>q14b</code>, which differs in the order of two local givens. The fix rejects both: each given can shadow the top-level one that the other needs, and no stable reading is found. <code>q14c</code> is accepted by both.",
   "Local givens are treated like top-level ones, so their order does not matter.",
   "If the order in a body is meant to matter, local givens must be excluded from the rounds."),
 ]),
 ("Overload resolution", [
  ("15", "Is the nested ranking of overloads intended?", False,
   "Only the outermost overloaded name of a statement is ranked across all combinations; the inner ones are ranked inside each choice of the outer one.",
   ["q15-nested-ranking.hylo"],
   "Accepted: <code>k(S.a(), S.b())</code> is an <code>X</code> and <code>k(S.b(), S.a())</code> is a <code>Y</code>. Unchanged.",
   "The existing ranking is preserved exactly.",
   "A ranking of whole combinations would be independent of the order of arguments."),
  ("16", "Should a solution with more errors than the best one stay viable?", False,
   "A preferred candidate with an error can win over one whose only diagnostic is a nested ambiguity.",
   ["q16-erroneous-candidate-wins.hylo"],
   "Rejected with the error of the preferred candidate (\"cannot pass value of type 'B' to parameter 'A'\"). Unchanged.",
   "The existing behaviour is preserved exactly.",
   "If only the candidates with the fewest diagnostics stayed viable, more of the search could be cut once a clean solution is known."),
  ("17", "Should a member and the trait requirement that it implements be two candidates?", False,
   "For a concrete receiver they denote the same function.",
   ["q17-member-and-requirement.hylo"],
   "Accepted. The existing solver makes 32,766 forks for 14 operators; with <span class=\"flag\">twins</span>, which shares the search between two candidates of the same type, 14.",
   "Both candidates are kept, and the second reuses the result of the first.",
   "If name resolution kept one candidate, the exponential cost would disappear at its source and <span class=\"flag\">twins</span> would not be needed."),
  ("18", "Are the diagnostics of an ill-typed statement part of the contract?", False,
   "May an implementation report a different, smaller set of errors for a statement that has none of the solutions?",
   [],
   "No program: the question is about what must be preserved.",
   "Yes: an erroneous statement is solved by the existing search, so that its diagnostics are unchanged. The overload techniques therefore speed up well-typed statements only.",
   "If the set of diagnostics may differ, erroneous statements can be made fast as well."),
 ]),
]

# (file, title, existing, fixed, document)
REPRO = [
 ("s1-unrelated-equalities.hylo", "1. Unrelated equalities make types interchangeable", "accepted", "rejected", "soundness/1-unrelated-equalities.md"),
 ("s1b-unrelated-equality-call.hylo", "", "accepted", "rejected", ""),
 ("s2-equality-chain.hylo", "2. Equality chains are slow or rejected", "accepted in 1.2 s", "accepted in 1.3 ms", "soundness/2-equality-chains.md"),
 ("s3-conditional-extension.hylo", "3. Associated types through a callee's requirements are not simplified", "accepted in 1.7 s", "accepted in 6.5 ms", "soundness/3-unsimplified-projections.md"),
 ("s4-cyclic-binding.hylo", "4. Cyclic type bindings crash the compiler", "crash (stack overflow)", "rejected", "soundness/4-cyclic-bindings.md"),
 ("s5-declaration-order.hylo", "5. Results depend on declaration order", "accepted in 9 of 24 orders", "accepted in 24 of 24", "soundness/5-declaration-order.md"),
 ("s6-generic-conformance.hylo", "6. Associated types of a generic conformance are one type for every instance", "accepted", "rejected", "soundness/6-generic-conformance-associated-types.md"),
 ("s7-self-projection.hylo", "7. Inside a trait, <code>Self.X</code> is equated with another witness's <code>T.X</code>", "accepted", "rejected", "soundness/7-self-projection.md"),
 ("s8-refinement.hylo", "8. A conformance satisfies the trait it refines with itself", "accepted", "rejected", "soundness/8-refinement-satisfied-by-itself.md"),
 ("s9-alias-arguments.hylo", "9. Members selected through an alias lose the type arguments", "accepted", "rejected", "soundness/9-members-through-aliases.md"),
]
COMPLETE = [
 ("c1-dependent-requirement.hylo", "Requirements that mention another requirement", "rejected", "accepted", "completeness/1-dependent-requirements.md"),
 ("c2-collection.hylo", "Associated types of a requirement in a signature", "rejected", "accepted", "completeness/2-projections-in-signatures.md"),
]

def question_html(q):
    qid, title, key, text, files, today, assumed, otherwise = q
    progs = ""
    for f in files:
        progs += f'<div class="prog"><div class="flag">questions/{f}</div><pre><code>{source("questions/" + f)}</code></pre></div>\n'
    mark = ' <span class="pill fix">decides most</span>' if key else ""
    return f'''    <div class="bug" id="q{qid}">
      <h3>{qid}. {title}{mark}</h3>
      <p>{text}</p>
{progs}      <dl>
        <dt>Today</dt><dd>{today}</dd>
        <dt>Assumed</dt><dd>{assumed}</dd>
        <dt>Otherwise</dt><dd>{otherwise}</dd>
      </dl>
    </div>
'''

def questions_section():
    out = ""
    for name, qs in GROUPS:
        out += f"    <h3 class=\"group\">{name}</h3>\n" + "".join(question_html(q) for q in qs)
    return out

def repro_rows(rows):
    out = ""
    for f, title, a, b, doc in rows:
        d = f'<a href="{doc}">details</a>' if doc else ""
        out += f'          <tr><td>{title}</td><td><code>{f}</code></td><td>{a}</td><td>{b}</td><td>{d}</td></tr>\n'
    return out

head = R("report.html").split("<main>")[0]
head = head.replace("<title>Hylo Type-Checker Optimizations</title>", "<title>Hylo type checker: findings and questions</title>")
head = head.replace("</style>", """h3.group { margin-top: 18px; font-size: 0.86rem; font-family: var(--font-mono); font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); }
.prog { display: grid; gap: 4px; }
.steps { display: grid; gap: 10px; padding-left: 1.4em; margin: 0; }
</style>""")

BODY = R("start-here.body.html")
BODY = BODY.replace("@@QUESTIONS@@", questions_section()).replace("@@REPRO@@", repro_rows(REPRO)).replace("@@COMPLETE@@", repro_rows(COMPLETE))
open(os.path.join(HERE, "START-HERE.html"), "w").write(head + BODY)

# questions/README.md
o = ["# Questions on the language, with a program for each\n",
     "The questions are stated in full in `../START-HERE.html`, section \"Questions\". This file lists the programs and what the type checker does with each. \"Existing\" is the implementation of `main`; \"recommended\" is the configuration of the report. `observed.txt` holds the raw output.\n"]
for name, qs in GROUPS:
    o.append(f"## {name}\n")
    for qid, title, key, text, files, today, assumed, otherwise in qs:
        o.append(f"**{qid}. {md(title)}**" + (" (one of the questions that decide most)" if key else "") + "\n")
        o.append(md(text) + "\n")
        if files: o.append("Programs: " + ", ".join(f"`{f}`" for f in files) + "\n")
        o.append("- Today: " + md(today))
        o.append("- Assumed by the fixes: " + md(assumed))
        o.append("- Otherwise: " + md(otherwise) + "\n")
open(os.path.join(HERE, "questions", "README.md"), "w").write("\n".join(o))

o = ["# Reproducers\n",
     "One small program per soundness problem of the existing implementation, and two for the valid programs that it rejects. Each file states the expected result in its first lines. `observed.txt` holds the raw output of both configurations; `../START-HERE.html` says how to run them.\n",
     "| Problem | Program | Existing implementation | With the fixes | Document |", "|---|---|---|---|---|"]
for f, title, a, b, doc in REPRO + COMPLETE:
    o.append(f"| {md(title)} | `{f}` | {a} | {b} | {('`../' + doc + '`') if doc else ''} |")
o.append("\nTimes are type-checking times of the user module on one core. Orders are orders of the top-level declarations, 24 tried.")
open(os.path.join(HERE, "reproducers", "README.md"), "w").write("\n".join(o) + "\n")
print("written")
