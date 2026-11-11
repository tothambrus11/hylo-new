# Reproducers

One small program per soundness problem of the existing implementation, and two for the valid programs that it rejects. Each file states the expected result in its first lines. `observed.txt` holds the raw output of both configurations; `../START-HERE.html` says how to run them.

| Problem | Program | Existing implementation | With the fixes | Document |
|---|---|---|---|---|
| 1. Unrelated equalities make types interchangeable | `s1-unrelated-equalities.hylo` | accepted | rejected | `../soundness/1-unrelated-equalities.md` |
|  | `s1b-unrelated-equality-call.hylo` | accepted | rejected |  |
| 2. Equality chains are slow or rejected | `s2-equality-chain.hylo` | accepted in 1.2 s | accepted in 1.3 ms | `../soundness/2-equality-chains.md` |
| 3. Associated types through a callee's requirements are not simplified | `s3-conditional-extension.hylo` | accepted in 1.7 s | accepted in 6.5 ms | `../soundness/3-unsimplified-projections.md` |
| 4. Cyclic type bindings crash the compiler | `s4-cyclic-binding.hylo` | crash (stack overflow) | rejected | `../soundness/4-cyclic-bindings.md` |
| 5. Results depend on declaration order | `s5-declaration-order.hylo` | accepted in 9 of 24 orders | accepted in 24 of 24 | `../soundness/5-declaration-order.md` |
| 6. Associated types of a generic conformance are one type for every instance | `s6-generic-conformance.hylo` | accepted | rejected | `../soundness/6-generic-conformance-associated-types.md` |
| 7. Inside a trait, `Self.X` is equated with another witness's `T.X` | `s7-self-projection.hylo` | accepted | rejected | `../soundness/7-self-projection.md` |
| 8. A conformance satisfies the trait it refines with itself | `s8-refinement.hylo` | accepted | rejected | `../soundness/8-refinement-satisfied-by-itself.md` |
| 9. Members selected through an alias lose the type arguments | `s9-alias-arguments.hylo` | accepted | rejected | `../soundness/9-members-through-aliases.md` |
| Requirements that mention another requirement | `c1-dependent-requirement.hylo` | rejected | accepted | `../completeness/1-dependent-requirements.md` |
| Associated types of a requirement in a signature | `c2-collection.hylo` | rejected | accepted | `../completeness/2-projections-in-signatures.md` |

Times are type-checking times of the user module on one core. Orders are orders of the top-level declarations, 24 tried.
