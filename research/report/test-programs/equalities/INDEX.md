# Test programs: equalities

Verdicts of the existing implementation, of the techniques with the fixes for problems 1 to 4 only, and of the recommended configuration of the report, with a 30 s limit (recommended configuration: 60 s).

| Program | Existing | Fixes 1–4 | Recommended | First error (recommended) |
|---|---|---|---|---|
| `c01-single-eq-call.hylo` | accepted | rejected | rejected | no coercion from '(D ~ V) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c02-no-eq-call.hylo` | timeout | rejected | rejected | no coercion from '(D ~ V) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c03-single-eq-given.hylo` | accepted | rejected | rejected | no coercion from 'P<D> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c04-single-assoc-call.hylo` | accepted | rejected | rejected | no coercion from '((D::P).X ~ (A::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c05-single-eq-both-unrelated.hylo` | timeout | rejected | rejected | no coercion from '(D ~ E) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c06-single-eq-struct.hylo` | accepted | rejected | rejected | no coercion from '(Q ~ S) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `c07-single-assoc-arg.hylo` | accepted | rejected | rejected | no coercion from '((D::P).X ~ (A::P).X) ==> [Void](let (D::P).X) let -> (A::P).X' to '[Void](let (D::P).X) let -> (A::P).X' |
| `v01-single.hylo` | rejected | rejected | rejected | cannot pass value of type '(D::P).X' to parameter '(A::P).X' |
| `v02-params.hylo` | accepted | rejected | rejected | cannot pass value of type 'D' to parameter 'A' |
| `v03-box.hylo` | accepted | rejected | rejected | cannot pass value of type 'Box<(D::P).X>' to parameter 'Box<(A::P).X>' |
| `v04-boxside.hylo` | accepted | rejected | rejected | cannot pass value of type 'D' to parameter 'A' |
| `v05-single-struct.hylo` | rejected | rejected | rejected | cannot pass value of type 'D' to parameter 'A' |
| `v06-onesided.hylo` | rejected | rejected | rejected | cannot pass value of type 'E' to parameter 'A' |
| `v07-samegiven.hylo` | accepted | accepted | accepted |  |
| `n-nested-1.hylo` | accepted | rejected | rejected | cannot pass value of type 'Box<(D::P).X>' to parameter 'Box<(A::P).X>' |
| `n-params-1.hylo` | accepted | rejected | rejected | cannot pass value of type 'D' to parameter 'A' |
| `n-params-2.hylo` | accepted | rejected | rejected | no coercion from '(A ~ D) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `n-params-3.hylo` | accepted | rejected | rejected | cannot pass value of type 'Box<D>' to parameter 'Box<A>' |
| `n-three-1.hylo` | accepted | rejected | rejected | cannot pass value of type '(F::P).X' to parameter '(A::P).X' |
| `n-tuple-1.hylo` | timeout | rejected | rejected | cannot pass value of type '{(D::P).X, (B::P).X}' to parameter '{(A::P).X, (A::P).X}' |
| `v-abs-1.hylo` | rejected | accepted | rejected | no coercion from '((Self::P).X ~ (T::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v-abs-2.hylo` | accepted | accepted | rejected | cannot pass value of type '(Self::P).X' to parameter '(T::P).X' |
| `v-abs-3.hylo` | rejected | accepted | rejected | no coercion from '((Self::P).X ~ (T::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v-abs-4.hylo` | rejected | accepted | rejected | no coercion from '((Self::P).X ~ (T::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v-abs-5.hylo` | rejected | rejected | rejected | cannot pass value of type '(Self::P).X' to parameter 'U' |
| `v-abs-6.hylo` | rejected | rejected | rejected | cannot pass value of type 'U' to parameter '(Self::P).X' |
| `v-abs-7.hylo` | accepted | accepted | rejected | no coercion from '((Self::P).X ~ U) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v-abs-8.hylo` | rejected | rejected | rejected | no coercion from '(#! ~ U) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v-abs-9.hylo` | rejected | rejected | rejected | cannot pass value of type 'U' to parameter '(Self::P).X' |
| `v-alias-1.hylo` | accepted | accepted | accepted |  |
| `v-alias-2.hylo` | accepted | accepted | accepted |  |
| `v-alias-3.hylo` | accepted | accepted | accepted |  |
| `v-chain-1.hylo` | accepted | accepted | accepted |  |
| `v-chain-2.hylo` | accepted | accepted | accepted |  |
| `v-chain3-assoc.hylo` | accepted | accepted | accepted |  |
| `v-chain3-mixed.hylo` | accepted | accepted | accepted |  |
| `v-chain3-par.hylo` | accepted | accepted | accepted |  |
| `v-congr-1.hylo` | timeout | rejected | rejected | no coercion from '((T::P).X ~ (U::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v-congr-2.hylo` | rejected | rejected | rejected | cannot pass value of type '(U::P).X' to parameter '(T::P).X' |
| `v-congr-3.hylo` | accepted | accepted | accepted |  |
| `v-congr-4.hylo` | accepted | accepted | accepted |  |
| `v-congr-5.hylo` | accepted | accepted | accepted |  |
| `v-congr-6.hylo` | accepted | accepted | accepted |  |
| `v-def-1.hylo` | accepted | accepted | accepted |  |
| `v-def-2.hylo` | accepted | accepted | accepted |  |
| `v-def-3.hylo` | timeout | rejected | rejected | no coercion from '((T::P).X ~ Bool) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `v-def-4.hylo` | accepted | accepted | accepted |  |
| `assoceq-1.hylo` | accepted | accepted | accepted |  |
| `assoceq-2.hylo` | accepted | accepted | accepted |  |
| `assoceq-3.hylo` | accepted | accepted | accepted |  |
| `assoceq-4.hylo` | accepted | accepted | accepted |  |
| `assoceq-5.hylo` | accepted | accepted | accepted |  |
| `assoceq-6.hylo` | accepted | accepted | accepted |  |
| `trans-1.hylo` | accepted | accepted | accepted |  |
| `trans-2.hylo` | accepted | accepted | accepted |  |
| `trans-3.hylo` | accepted | accepted | accepted |  |
| `trans-4.hylo` | accepted | accepted | accepted |  |
| `trans-5.hylo` | accepted | accepted | accepted |  |
| `trans-6.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-assoceq-2.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-assoceq-3.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-assoceq-4.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-assoceq-5.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-assoceq-6.hylo` | accepted | accepted | accepted |  |
| `assoceq-8.hylo` | accepted | accepted | accepted |  |
| `assocneg-2.hylo` | rejected | rejected | rejected | cannot pass value of type '(T2::P).X' to parameter '(T0::P).X' |
| `assocneg-3.hylo` | accepted | rejected | rejected | cannot pass value of type '(T3::P).X' to parameter '(T0::P).X' |
| `assocneg-4.hylo` | accepted | rejected | rejected | cannot pass value of type '(T4::P).X' to parameter '(T0::P).X' |
| `assocneg-5.hylo` | accepted | rejected | rejected | cannot pass value of type '(T5::P).X' to parameter '(T0::P).X' |
| `assocneg-6.hylo` | accepted | rejected | rejected | cannot pass value of type '(T6::P).X' to parameter '(T0::P).X' |
| `assocneg-8.hylo` | accepted | rejected | rejected | cannot pass value of type '(T8::P).X' to parameter '(T0::P).X' |
| `cong-0.hylo` | accepted | accepted | accepted |  |
| `cong-1.hylo` | accepted | accepted | accepted |  |
| `cong-2.hylo` | accepted | accepted | accepted |  |
| `decomp-1.hylo` | accepted | accepted | accepted |  |
| `decomp-2.hylo` | rejected | rejected | rejected | no coercion from 'P<Box<B>> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `decomp-3.hylo` | accepted | accepted | accepted |  |
| `eqbug1-plain.hylo` | accepted | rejected | rejected | cannot pass value of type '(D::P).X' to parameter '(A::P).X' |
| `eqbug1-struct.hylo` | accepted | rejected | rejected | cannot pass value of type '(D::P).X' to parameter '(A::P).X' |
| `open-1.hylo` | accepted | accepted | accepted |  |
| `open-2.hylo` | accepted | accepted | accepted |  |
| `open-3.hylo` | accepted | accepted | accepted |  |
| `open-4.hylo` | accepted | accepted | accepted |  |
| `openchain-4.hylo` | accepted | accepted | accepted |  |
| `openchain-5.hylo` | accepted | accepted | accepted |  |
| `quant-1.hylo` | accepted | accepted | accepted |  |
| `quant-2.hylo` | rejected | rejected | rejected | cannot pass value of type 'C' to parameter 'Box<B>' |
| `quant-2b.hylo` | accepted | accepted | accepted |  |
| `quant-2c.hylo` | rejected | rejected | rejected | cannot pass value of type 'C' to parameter 'Box<B>' |
| `quant-2d.hylo` | accepted | accepted | accepted |  |
| `quant-3.hylo` | accepted | accepted | accepted |  |
| `quant-4.hylo` | rejected | rejected | rejected | cannot pass value of type 'A' to parameter 'B' |
| `eqchain-fix-trans-2.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-trans-3.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-trans-4.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-trans-5.hylo` | accepted | accepted | accepted |  |
| `eqchain-fix-trans-6.hylo` | accepted | accepted | accepted |  |
| `trans-8.hylo` | accepted | accepted | accepted |  |
| `transconf-2.hylo` | accepted | accepted | accepted |  |
| `transconf-3.hylo` | accepted | accepted | accepted |  |
| `transconf-4.hylo` | accepted | accepted | accepted |  |
| `transconf-5.hylo` | accepted | accepted | accepted |  |
| `transconf-6.hylo` | accepted | accepted | accepted |  |
| `transconf-8.hylo` | accepted | accepted | accepted |  |
| `transneg-2.hylo` | rejected | rejected | rejected | cannot pass value of type '(T2::P).X' to parameter '(T0::P).X' |
| `transneg-3.hylo` | rejected | rejected | rejected | cannot pass value of type '(T3::P).X' to parameter '(T0::P).X' |
| `transneg-4.hylo` | rejected | rejected | rejected | cannot pass value of type '(T4::P).X' to parameter '(T0::P).X' |
| `transneg-5.hylo` | rejected | rejected | rejected | cannot pass value of type '(T5::P).X' to parameter '(T0::P).X' |
| `transneg-6.hylo` | rejected | rejected | rejected | cannot pass value of type '(T6::P).X' to parameter '(T0::P).X' |
| `transneg-8.hylo` | rejected | rejected | rejected | cannot pass value of type '(T8::P).X' to parameter '(T0::P).X' |
| `a01-self-trait.hylo` | accepted | accepted | accepted |  |
| `a02-conformance-def.hylo` | accepted | accepted | accepted |  |
| `a03-generic-given-body.hylo` | rejected | rejected | rejected | no coercion from 'P<V> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `a04-cond-given.hylo` | accepted | accepted | accepted |  |
| `a05-quantified.hylo` | rejected | accepted | accepted |  |
| `a06-tuple-arrow.hylo` | rejected | accepted | accepted |  |
| `a07-open.hylo` | accepted | accepted | accepted |  |
| `a08-assoc-generic.hylo` | accepted | accepted | accepted |  |
| `a09-conf-via-eq.hylo` | accepted | accepted | accepted |  |
| `e01-orient-amb.hylo` | accepted | accepted | accepted |  |
| `e01b-both-direct.hylo` | rejected | rejected | rejected | no coercion from 'P<A> ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `e02-penalty.hylo` | accepted | accepted | accepted |  |
| `e03-penalty2.hylo` | accepted | accepted | accepted |  |
| `e04-penalty-scope.hylo` | accepted | accepted | accepted |  |
| `e05-penalty-scope2.hylo` | accepted | accepted | accepted |  |
| `e06-elab-change.hylo` | accepted | accepted | accepted |  |
| `e07-refine.hylo` | rejected | rejected | rejected | no coercion from '(#! ~ U) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `e08-shapes.hylo` | timeout | accepted | accepted |  |
| `e09-trait-self-assoc.hylo` | accepted | accepted | accepted |  |
| `o1-open-chain.hylo` | accepted | accepted | accepted |  |
| `o2-open-chain.hylo` | accepted | accepted | accepted |  |
| `o2b-call-infer.hylo` | accepted | accepted | accepted |  |
| `o2c-call-explicit.hylo` | accepted | accepted | accepted |  |
| `o2d-order.hylo` | accepted | accepted | accepted |  |
| `o3-open-chain.hylo` | accepted | accepted | accepted |  |
| `o4-open-chain.hylo` | accepted | accepted | accepted |  |
| `o5-open-chain.hylo` | accepted | accepted | accepted |  |
| `p01-cc-big.hylo` | timeout | accepted | accepted |  |
| `p02-cc-big.hylo` | timeout | accepted | accepted |  |
| `x01-ext-arg-member.hylo` | accepted | accepted | accepted |  |
| `x02-ext-nested.hylo` | accepted | accepted | accepted |  |
| `x03-ext-nested-struct.hylo` | accepted | accepted | accepted |  |
| `x04-generic-ext-where.hylo` | rejected | rejected | rejected | expression does not denote a type |
| `x05-alias-ext.hylo` | accepted | accepted | accepted |  |
| `x06-nested-ext-no-alias.hylo` | accepted | accepted | accepted |  |
| `x07-given-arg-member.hylo` | accepted | accepted | accepted |  |
| `x08-ext-arg-member-reordered.hylo` | accepted | accepted | accepted |  |
| `x09-ext-generic-where-assoc.hylo` | accepted | accepted | accepted |  |
| `x10-ext-where-assoc.hylo` | timeout | rejected | accepted |  |
| `x10b-ext-where-assoc.hylo` | accepted | accepted | accepted |  |
| `x11-ext-forward.hylo` | accepted | accepted | accepted |  |
| `x12-ext-members-kinds.hylo` | rejected | rejected | rejected | no candidate matches the argument list |
| `x13-ext-body-lookup.hylo` | rejected | rejected | rejected | incompatible labels: found '(other:)', expected '(_:)' |
| `x14-ext-generic-arg-assoc-std.hylo` | rejected | rejected | rejected | undefined symbol 'Array' |
| `eq-regress-judge-e04-penalty-scope.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-e05-penalty-scope2.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-e06-elab-change.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-o2-open-chain.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-o2b-call-infer.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-o2d-order.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-p01-cc-big.hylo` | timeout | accepted | accepted |  |
| `eq-regress-judge-p02-cc-big.hylo` | timeout | accepted | accepted |  |
| `eq-regress-judge-x01-ext-arg-member.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-x03-ext-nested-struct.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-x06-nested-ext-no-alias.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-x09-ext-generic-where-assoc.hylo` | accepted | accepted | accepted |  |
| `eq-regress-judge-x10b-ext-where-assoc.hylo` | accepted | accepted | accepted |  |
| `abs-launder-2.hylo` | rejected | rejected | rejected | cannot pass value of type '(W::P).X' to parameter '(V::P).X' |
| `abs-launder-3.hylo` | rejected | rejected | rejected | cannot pass value of type '(W::P).X' to parameter '(V::P).X' |
| `abs-launder-direct.hylo` | rejected | rejected | rejected | cannot pass value of type '(W::P).X' to parameter '(V::P).X' |
| `abs-launder.hylo` | rejected | rejected | rejected | no coercion from '(T::P).X' to '(Self::P).X' |
| `abs-trans-0.hylo` | rejected | rejected | rejected | cannot pass value of type '(U::P).X' to parameter '(T::P).X' |
| `abs-trans-1.hylo` | rejected | rejected | rejected | cannot pass value of type '(U::P).X' to parameter '(T::P).X' |
| `abs-trans-2.hylo` | accepted | rejected | rejected | no coercion from '((T::P).X ~ (U::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `abs-trans-3.hylo` | accepted | rejected | rejected | no coercion from '((U::P).X ~ (T::P).X) ==> [Void](let (U::P).X) let -> (T::P).X' to '[Void](let (U::P).X) let -> (T::P).X' |
| `abs-trans-4.hylo` | timeout | rejected | rejected | no coercion from '((U::P).X ~ (T::P).X) ==> [Void](let (U::P).X) let -> (T::P).X' to '[Void](let (U::P).X) let -> (T::P).X' |
| `abs-trans-5.hylo` | timeout | rejected | rejected | no coercion from '((U::P).X ~ (T::P).X) ==> [Void](let (U::P).X) let -> (T::P).X' to '[Void](let (U::P).X) let -> (T::P).X' |
| `absinst-0.hylo` | accepted | rejected | rejected | no coercion from '((V::P).X ~ Bool) ==> [let V]() let -> Void' to '[let V]() let -> Void' |
| `absinst-1.hylo` | accepted | rejected | rejected | no coercion from '((V::P).X ~ Bool) ==> [let V]() let -> Void' to '[let V]() let -> Void' |
| `absinst-ok.hylo` | accepted | accepted | accepted |  |
| `absleak-0.hylo` | accepted | accepted | accepted |  |
| `absleak-1.hylo` | rejected | rejected | rejected | cannot pass value of type '(T::P).X' to parameter '(U::P).X' |
| `absleak-2.hylo` | rejected | rejected | rejected | no coercion from '(T::P).X' to '(U::P).X' |
| `absleak-3.hylo` | timeout | rejected | rejected | no coercion from '(T::P).X' to '(U::P).X' |
| `absleak-4.hylo` | timeout | rejected | rejected | no coercion from '((T::P).X ~ (U::P).X) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `alias-hk-1.hylo` | rejected | rejected | rejected | 'B2' takes no compile-time arguments |
| `alias-hk-2.hylo` | rejected | rejected | rejected | 'B2' takes no compile-time arguments |
| `alias-proj-1.hylo` | rejected | rejected | rejected | where clause is not allowed here |
| `ate-f1.hylo` | accepted | accepted | accepted |  |
| `ate.hylo` | accepted | accepted | accepted |  |
| `ati.hylo` | rejected | rejected | rejected | cannot pass value of type '(U::P).X' to parameter '(T::P).X' |
| `dump-1.hylo` | accepted | accepted | accepted |  |
| `extwhere-1.hylo` | rejected | rejected | rejected | type '{B, B}' has no member 'm' |
| `extwhere-1ok.hylo` | accepted | accepted | accepted |  |
| `extwhere-2.hylo` | rejected | rejected | rejected | no coercion from '<T> T ==> [Void](let Metatype<T>) let -> yield T' to '[Void](let Metatype<P<{B, B}>>) let -> yield P<{B, B}>' |
| `extwhere-3.hylo` | accepted | accepted | accepted |  |
| `nested-eq.hylo` | timeout | rejected | rejected | expected 'is' |
| `pen-1.hylo` | rejected | rejected | rejected | cannot pass value of type '(W::P).X' to parameter 'A' |
| `pen-2.hylo` | rejected | rejected | rejected | no coercion from 'A' to '(W::P).X' |
| `pen-ref-1.hylo` | rejected | rejected | rejected | no coercion from 'A' to '(W::P).X' |
| `pen-ref-2.hylo` | rejected | rejected | rejected | no coercion from 'A' to '(W::P).X' |
| `pen-ref-3.hylo` | rejected | accepted | accepted |  |
| `pen-ref-4.hylo` | accepted | accepted | accepted |  |
| `pend-1.hylo` | timeout | rejected | rejected | no coercion from '<T> T ==> [Void](let Metatype<T>) let -> yield T' to '[Void](let Metatype<P<C>>) let -> yield P<C>' |
| `pend-2.hylo` | timeout | rejected | rejected | no coercion from '<T> T ==> [Void](let Metatype<T>) let -> yield T' to '[Void](let Metatype<P<C>>) let -> yield P<C>' |
| `perf-alias-7.hylo` | rejected | accepted | accepted |  |
| `perf-alias.hylo` | rejected | accepted | accepted |  |
| `perf-deep-100.hylo` | rejected | accepted | accepted |  |
| `perf-deep-200.hylo` | rejected | accepted | accepted |  |
| `perf-deep-50.hylo` | rejected | accepted | accepted |  |
| `structwhere-1.hylo` | rejected | rejected | rejected | incompatible labels: found '(x:)', expected '(_:)' |
| `structwhere-2.hylo` | rejected | rejected | rejected | where clause is not allowed here |
| `eq-unsound-v-abs-7.hylo` | accepted | accepted | rejected | no coercion from '((Self::P).X ~ U) ==> [Void]() let -> Void' to '[Void]() let -> Void' |
| `mirror-0.hylo` | accepted | accepted | accepted |  |
| `mirror-1.hylo` | rejected | rejected | rejected | no coercion from 'A' to '(W::P).X' |
| `mirror-2.hylo` | rejected | rejected | rejected | no given instance of 'Q1<W>' in this scope |
| `eqbug-1.hylo` | accepted | rejected | rejected | cannot pass value of type '(D::P).X' to parameter '(A::P).X' |
| `eqbug-2.hylo` | accepted | rejected | rejected | cannot pass value of type '(C::P).X' to parameter '(B::P).X' |
| `eqbug-3.hylo` | accepted | rejected | rejected | cannot pass value of type '(D::Q).Y' to parameter '(A::P).X' |
| `eqbug-4.hylo` | accepted | rejected | rejected | no coercion from '(D::P).X' to '(A::P).X' |
| `eqbug-5.hylo` | accepted | accepted | accepted |  |
| `bug-assoc-eq-two-links.hylo` | accepted | rejected | rejected | cannot pass value of type '(D::P).X' to parameter '(A::P).X' |
| `assoc-eq-call-incomplete.hylo` | timeout | rejected | accepted |  |
