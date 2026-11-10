# Results

Binary `eq22-554540c3a507`. Columns are configurations of `run.py` (`X-flag` is X without the flag, `X+flag` is X with it).
Raw records, with every diagnostic: `results.jsonl`. Regenerate with `python3 tabulate.py`.

## Attack programs (`p/`)

| program | base | FULL | NEW | NEW+selfcheck | FULL+assocsubst | NEW-assocsubst | FULL+abstractstrict | NEW-abstractstrict | FULL+headsubst | NEW-headsubst | what it tests |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `p/a01-term-witness.hylo` | reject(2) | reject(2) | reject(2) | reject(2) | reject(2) | reject(2) | reject(2) | reject(2) |  |  | assocsubst: the associated type is defined by an associated type of the parameter (type X = T.Y); |
| `p/a02-term-witness-twin.hylo` | accept | accept | accept | accept | reject(1) | accept | accept | accept |  | reject(1) | assocsubst + headsubst: Box<V>.X is (V::q).Y and Box<W>.X is (W::q).Y, where q is the premise |
| `p/a02c-term-witness-twin-ctl.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) |  |  | Control of a02: the direct conversion of V.Y into W.Y, which the language rejects. |
| `p/a03-value-crossing.hylo` | accept | accept | accept | accept | reject(1) | accept | accept | accept |  | reject(1) | assocsubst + headsubst: a value of type S0 reaches a function that expects an S1. |
| `p/a04-nested-scopes.hylo` | accept | accept | accept | accept | accept | accept | accept | accept |  |  | assocsubst alone (no headsubst needed): Box<A>.X is (A::q).Y in every scope, whatever witness |
| `p/a04c-nested-scopes-ctl.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) |  |  | Control of a04: the same flow with a ground conformance of Box<A> in each scope is rejected. |
| `p/a05-param-not-in-head.hylo` | reject(3) | reject(3) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: a parameter of the conformance that does not occur in its head defines X. |
| `p/a05b-param-not-in-head-pair.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | assocsubst: the undetermined parameter U makes Box<S0>.X and Box<S1>.X the error type. |
| `p/a05c-param-not-in-head-value.hylo` | accept | accept | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: with get/put, does a value cross between two instances when X is an undetermined parameter? |
| `p/a05d-param-not-in-head-methods.hylo` | reject(4) | reject(4) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: X is a parameter U that does not occur in the head. Through the methods, is |
| `p/a05e-param-not-in-head-lets.hylo` | reject(2) | reject(2) | accept | accept | accept | reject(2) | reject(2) | accept |  |  | assocsubst: X is a parameter U that does not occur in the head. The result of get() on the |
| `p/a05f-param-not-in-head-ctl.hylo` | reject(2) | reject(2) | reject(1) | reject(1) | reject(1) | reject(2) | reject(2) | reject(1) |  |  | Control of a05e: X is the parameter of the head; the second binding is rejected. |
| `p/a06-two-params.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: two parameters, the associated type is the second one. Line 11 is valid, 12 and 13 are not. |
| `p/a06v-two-params-valid.hylo` | reject(3) | reject(3) | accept | accept |  |  |  |  |  |  | assocsubst: two parameters; every line is valid. |
| `p/a07-nested-box.hylo` | reject(5) | reject(5) | accept | accept |  |  |  |  |  |  | assocsubst: Box<Box<S0>>.X is Box<S0>, and (Box<Box<S0>>.X).X is S0. Lines "bad" are invalid. |
| `p/a07n-nested-box-neg.hylo` | reject(3) | reject(3) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: Box<Box<S0>>.X is Box<S0>; each function is invalid (three errors expected). |
| `p/a08-pair-of-param.hylo` | reject(3) | reject(3) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: the associated type is a type application of the parameter (type X = Pair<T, T>). |
| `p/a09-bare-param.hylo` | reject(5) | reject(5) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: conformance of a bare parameter with a compound definition. |
| `p/a10-adjunct.hylo` | reject(8) | reject(8) | reject(8) | reject(8) |  |  |  |  |  |  | assocsubst: adjunct conformance of a generic struct; the associated type is a member of the struct. |
| `p/a11-refinement.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: the associated type of P is reached through a conformance to a trait that refines P. |
| `p/a11b-refinement-silent.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | The associated type of P reached through a requirement `B is R`, where R refines P, is the |
| `p/a12-trait-param.hylo` | reject(3) | reject(3) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: trait with a parameter; the definition uses the conformance parameters in both positions. |
| `p/a13-struct-in-conformance.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | assocsubst: the associated type is a struct declared inside the generic conformance. |
| `p/a13b-struct-in-conformance-field.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: the struct declared in the generic conformance holds a T. Through Box<S0>, its field |
| `p/a13c-struct-in-generic-struct.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | Not assocsubst: a struct nested in a generic struct that mentions its parameter, for comparison with a13. |
| `p/a14-member-alias.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | assocsubst: the definition goes through a member alias of the generic struct (type X = Self.Elem). |
| `p/a14c-member-alias-struct-only.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | Not assocsubst: a member alias of a generic struct (type Elem = T), for comparison with a14. |
| `p/a14d-member-alias-value.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | assocsubst: type X = Self.Elem with implementations that read and write the stored T. |
| `p/a14v-member-alias-valid.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: as a14, valid use: Box<S0>.X is Box<S0>.Elem, which is S0. |
| `p/a15-alias-chain.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: alias chain inside the conformance (type X = Z, type Z = W, type W = T) and a global alias. |
| `p/a16-generic-alias.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: the definition is an application of a generic alias (type X = Twice<T>). |
| `p/a17-recursive-conditional.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: recursive conditional conformance, type X = Box<T.X>. |
| `p/a18-pick.hylo` | reject(10) | reject(10) | accept | accept |  |  |  |  |  |  | assocsubst + headsubst: the result of pick is T.X; with T = Box<S0> it is S0. |
| `p/a18n-pick-neg.hylo` | reject(8) | reject(8) | reject(4) | reject(4) |  |  |  |  |  |  | assocsubst + headsubst: four invalid uses (one error expected in each function). |
| `p/a19-param-twice.hylo` | reject(2) | reject(2) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: the parameter occurs twice in the head. ok is valid; bad is invalid (Pair<S0, S1> does not conform). |
| `p/a20-nested-head.hylo` | reject(4) | reject(4) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: the head is Box<Box<T>> and X = T. ok valid, bad invalid. |
| `p/a21-tuple-arrow.hylo` | reject(4) | reject(4) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: the definition is a tuple and a function type of the parameters. |
| `p/a22-bare-param-where.hylo` | reject(2) | reject(2) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: conformance of a bare parameter with a requirement, type X = A.Y. |
| `p/a23-conformance-mismatch.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: an implementation whose type does not match the requirement once X is known. Invalid (2 conformances). |
| `p/a24-inside-conformance.hylo` | reject(2) | reject(2) | accept | accept |  |  |  |  |  |  | assocsubst: inside the conformance, its own instance at Box<Box<T>> (the argument mentions the parameter). |
| `p/a24n-inside-conformance-neg.hylo` | accept | accept | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: as a24, invalid: Box<Box<T>>.X is Box<T>, not T (2 errors expected). |
| `p/a25-param-through-premise.hylo` | reject(2) | reject(2) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: X is a parameter U determined only by a premise (T.Y == U). ok is valid, bad is invalid. |
| `p/a26-param-through-trait-arg.hylo` | reject(2) | reject(2) | reject(1) | reject(1) | reject(1) | reject(2) | reject(2) | reject(1) |  |  | assocsubst: X is a parameter U that does not occur in the head and is determined by the |
| `p/a26b-param-through-trait-arg-check.hylo` | reject(3) | reject(3) | reject(2) | reject(2) | reject(2) | reject(3) | reject(3) | reject(2) |  |  | As a26 with the result passed to a function instead of bound: bad2 passes the S1 where an S0 is expected. |
| `p/a27-param-ambiguous-premise.hylo` | reject(6) | reject(6) | reject(2) | reject(2) | reject(2) | reject(6) | reject(6) | reject(2) |  |  | assocsubst: X is a parameter U determined by a premise that has two solutions |
| `p/b10-refinement-twin.hylo` | accept | accept | accept | accept | accept | accept | accept | accept |  |  | abstractstrict: the requirements of P reached through a refinement R. w.get() is a W.X through |
| `p/b10c-refinement-twin-ctl.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) |  |  | Control of b10: the same flow with requirements on P itself is rejected. |
| `p/b10d-refinement-no-equality.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) |  |  | Control of b10 without V == W: rejected. |
| `p/b11-refinement-twin-value.hylo` | accept | accept | accept | accept | accept | accept | accept | accept |  |  | b10 with concrete types: an S1 reaches a function that expects an S0. |
| `p/b12-launder-refinement.hylo` | accept | accept | accept | accept |  |  |  | accept |  | accept | abstractstrict: launder-5 with the second conformance stated through a refinement (T is R). |
| `p/b12c-launder-refinement-ctl.hylo` | accept | accept | reject(1) | reject(1) |  |  |  | accept |  | reject(1) | Control of b12: the second conformance is to P itself; the body of `cast` is rejected. |
| `p/c01-capture.hylo` | reject(1) | reject(1) | accept | accept | accept | reject(1) | reject(1) | accept |  |  | assocsubst: substitution capturing a bound parameter. In the body of the requirement m<U>, |
| `p/c01c-capture-ctl.hylo` | reject(2) | reject(2) | reject(1) | reject(1) | reject(1) | reject(2) | reject(2) | reject(1) |  |  | Control of c01: the called requirement m2 has its own parameter W, so nothing can be captured. |
| `p/c01v-capture-valid.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) |  |  | assocsubst: as c01 with the valid binding: the call returns a Box<U>.X, which is U. |
| `p/c02-capture-value.hylo` | reject(2) | reject(2) | accept | accept | accept | reject(2) | reject(2) | accept |  |  | c01 with concrete types: main calls m<S1>; inside, b is a Box<S1> and b.m<S0>(...) returns |
| `p/d01-equality-premise.hylo` | reject(4) | reject(4) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: conformance with an equality premise (T == U), X = U. ok valid; bad1 and bad2 invalid (2 errors expected). |
| `p/d02-ground-equality-premise.hylo` | reject(4) | reject(4) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: conformance with a premise T == S0. ok valid; bad1, bad2 invalid (2 errors expected). |
| `p/d03-tuple-head.hylo` | reject(2) | reject(2) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: the head of the conformance is a tuple type. ok valid; bad invalid (1 error expected). |
| `p/d04-alias-head.hylo` | reject(4) | reject(4) | reject(4) | reject(4) |  |  |  |  |  |  | assocsubst: the head of the conformance is written with a generic alias. ok valid; bad invalid (1 error expected). |
| `p/d05-member-order.hylo` | reject(2) | reject(2) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: the associated type is declared after the methods that use it. ok valid; bad invalid (1 error expected). |
| `p/e01-extension-from-generic.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | A method of an extension of the conforming types, called from a generic function. Valid. |
| `p/e02-extension-twin.hylo` | reject(1) | reject(1) | accept | accept |  | accept |  | accept | accept | reject(1) | Extension of the conforming types: w.one() is a W.X through W's witness, v.two expects a V.X |
| `p/e02c-extension-twin-ctl.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | Control of e02: the same flow through the requirements of the trait directly. |
| `p/e02d-extension-no-equality.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) |  |  | Control of e02 without V == W: rejected. |
| `p/e03-function-twin.hylo` | reject(2) | reject(2) | reject(1) | reject(1) |  |  |  |  |  |  | headsubst: the same flow as e02 through generic functions. |
| `p/e03b-function-twin-explicit.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | headsubst: as e03 with the type arguments written. |
| `p/e04-extension-twin-value.hylo` | reject(1) | reject(1) | accept | accept |  | accept |  | accept | accept | reject(1) | e02 with concrete types: an S1 reaches a function that expects an S0. |
| `p/e05-extension-concrete.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: methods of an extension of the conforming types, used at an instance of a generic conformance. |
| `p/e05n-extension-concrete-neg.hylo` | reject(3) | reject(3) | reject(3) | reject(3) |  |  |  |  |  |  | As e05, invalid uses (3 errors expected). |
| `p/k01-self-cycle.hylo` | reject(3) | reject(3) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: the associated type is defined by itself (type X = Self.X). Must be rejected without crash. |
| `p/k02-growing.hylo` | reject(1) | reject(1) | accept | accept |  |  |  |  |  |  | assocsubst: the associated type grows at each step (type X = Box<Box<T>>). Valid. |
| `p/k03-recursive-no-base.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: recursive conditional conformance without a base case; Box<S0> does not conform. Must be rejected. |
| `p/k04-polymorphic-recursion.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | assocsubst: a conformance of Box<T> that requires Box<Box<T>> is P (no derivation). Must be rejected without crash. |
| `p/k05-mutual.hylo` | reject(2) | reject(2) | accept | accept |  |  |  |  |  |  | assocsubst: two generic conformances whose associated types are defined through each other's methods. Valid. |
| `p/k05n-mutual-neg.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | As k05, invalid (2 errors expected). |
| `p/k06-deep-chain.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst + premsubst: a requirement chain nine associated types deep at a nested instance. Valid. |
| `p/k06n-deep-chain-neg.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | As k06, invalid: the fourth associated type is S0, not Box<S0> (1 error expected). |
| `p/k07-chain-2.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst + premsubst + headsubst: a requirement chain two associated types deep at a nested instance. Valid. |
| `p/k08-chain-3.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst + premsubst + headsubst: a requirement chain three associated types deep at a nested instance. Valid. |
| `p/k08b-chain-3-generic.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | premsubst + headsubst: the chain of k08 at a generic caller with the same requirements. Valid. |
| `p/k09-chain-2-generic.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | premsubst + headsubst: T.X.X in the parameters of the callee, at a generic caller with the same requirements. Valid. |
| `p/n01-given-in-generic-struct.hylo` | reject(3) | reject(3) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: a conformance declared inside a generic struct; its associated type is the parameter of the struct. |
| `p/n02-given-in-extension.hylo` | reject(3) | reject(3) | reject(3) | reject(3) |  |  |  |  |  |  | assocsubst: a conformance declared inside a generic extension; its associated type is the parameter of the extension. |
| `p/n03-given-in-generic-function.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | assocsubst: a conformance declared inside a generic function; its associated type is the parameter of the function. |
| `p/o01-head-through-assoc.hylo` | reject(3) | reject(3) | accept | accept |  |  |  |  |  |  | assocsubst + sigrounds: the head of a conformance and of an extension is an instantiated associated type (Box<S0>.X = S0). Valid. |
| `p/o01n-head-through-assoc-neg.hylo` | reject(3) | reject(3) | reject(2) | reject(2) |  |  |  |  |  |  | As o01, invalid: S1 is not Q and has no member hello (2 errors expected). |
| `p/o02-dependent-premise.hylo` | reject(1) | reject(1) | accept | accept |  |  |  |  |  |  | assocsubst + premsubst: a conditional conformance whose second requirement is about the associated type of the first. Valid. |
| `p/o02n-dependent-premise-neg.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | As o02, invalid: Box<S1>.X is S1, which is not Q; Box<Box<S0>>.X is Box<S0>, which is not Q (2 errors expected). |
| `p/o03-param-order.hylo` | reject(2) | reject(2) | accept | accept |  |  |  |  |  |  | assocsubst: the parameters of the conformance are declared in the other order than they occur in the head. Valid. |
| `p/o03n-param-order-neg.hylo` | reject(2) | reject(2) | reject(2) | reject(2) |  |  |  |  |  |  | As o03, invalid (2 errors expected). |
| `p/r01-nested-given.hylo` | accept | accept | reject(1) | reject(1) | accept | reject(1) | reject(1) | accept |  |  | abstractstrict: a given nested in a trait about its associated type (type X ; given X is Q). |
| `p/r01c-nested-given-ctl.hylo` | accept | accept | accept | accept | accept | accept | accept | accept |  |  | Control of r01: the same goal inside the trait, through the witness being declared. |
| `p/r02-trait-calls-generic.hylo` | reject(1) | reject(1) | accept | accept |  |  |  |  |  |  | abstractstrict: a method of the trait passes self and a Self.X to a generic function that |
| `p/r02b-trait-calls-generic-explicit.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | abstractstrict: as r02 with the type argument written. |
| `p/r03-trait-calls-pick.hylo` | reject(2) | reject(2) | accept | accept |  |  |  |  |  |  | abstractstrict: a method of the trait returns the result of a generic function whose result is T.X. Valid. |
| `p/r04-self-equal-param.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | abstractstrict: T == Self without a second conformance: T.X is selected through the witness |
| `p/r05-trait-calls-extension.hylo` | accept | accept | reject(1) | reject(1) | accept | reject(1) | reject(1) | accept |  |  | abstractstrict: a method of the trait calls a method of an extension of the conforming types. Valid. |
| `p/r06-explicit-equality.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | abstractstrict: a requirement of the trait with its own parameter and where clause that states |
| `p/r07-other-self.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | abstractstrict: methods of the trait applied to another value of type Self. Valid. |
| `p/r08-method-on-equal-param.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | abstractstrict: a value of type T with T == Self (and no second conformance) uses the |
| `p/r09-conformance-uses-default.hylo` | reject(1) | reject(1) | accept | accept |  |  |  |  |  |  | abstractstrict + assocsubst: a default method of the trait seen through a generic conformance. |
| `p/r09n-conformance-uses-default-neg.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  |  |  |  |  | As r09 with an invalid use: Box<S0>.dup() is an S0, not an S1. |
| `p/r10-trait-two-values.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | abstractstrict: inside the trait, a generic requirement on a second type that conforms to P; |
| `p/r11-conditional-given-on-assoc.hylo` | accept | accept | reject(1) | reject(1) | accept | reject(1) | reject(1) | accept |  |  | abstractstrict: a generic given whose head mentions T.X, used in the body of the trait at T = Self. |
| `p/r11b-conditional-given-on-assoc-generic.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) | reject(1) |  |  | The goal of r11 in a generic function instead of the trait body. Valid. |
| `p/r12-trait-calls-dependent.hylo` | accept | accept | accept | accept | accept | accept | reject(1) | accept |  |  | abstractstrict + premsubst: the trait body calls a function that requires T is P, T.X is Q at T = Self; |
| `p/r13-nested-given-in-extension.hylo` | accept | accept | reject(1) | reject(1) | accept | reject(1) | reject(1) | accept |  |  | abstractstrict: the nested given of r01 used in an extension of the conforming types. Valid. |
| `p/r16-conditional-conformance-on-self.hylo` | reject(1) | reject(1) | reject(1) | reject(1) | accept | reject(1) | reject(1) | accept |  |  | abstractstrict + assocsubst: the trait body uses a conditional conformance of Self whose associated type is T.X. Valid. |
| `p/r22-method-on-assoc-value.hylo` | accept | accept | reject(1) | reject(1) | accept | reject(1) | reject(1) | accept |  |  | abstractstrict: a method of Q called on a value of type T.X, where the trait P states X is Q |
| `p/r22c-method-on-assoc-value-ctl.hylo` | accept | accept | accept | accept | accept | accept | accept | accept |  |  | Control of r22: the same call in the body of the trait. |
| `p/r23-nested-given-concrete.hylo` | reject(2) | reject(2) | accept | accept | accept | reject(2) | reject(2) | accept |  |  | abstractstrict + assocsubst: the nested given of r01 at an instance of a generic conformance. Valid. |
| `p/r24-extension-equality-from-trait.hylo` | accept | accept | accept | accept |  |  | accept | accept |  |  | abstractstrict + premsubst: an extension of the conforming types that requires T.X == S0, |
| `p/r25-nested-given-compound.hylo` | accept | accept | reject(1) | reject(1) |  |  | reject(1) | accept |  |  | abstractstrict: a nested given about a type built from the associated type (given Box<X> is Q). Valid. |
| `p/r26-extension-of-box-from-trait.hylo` | accept | accept | reject(1) | reject(1) |  |  | reject(1) | accept |  |  | abstractstrict: an extension of Box<T> for T is P with a parameter of type T.X, called in the body of the trait on a Box<Self>. Valid. |
| `p/r26b-extension-of-box-from-generic.hylo` | reject(1) | reject(1) | reject(1) | reject(1) |  |  | reject(1) | reject(1) |  |  | The call of r26 from a generic function instead of the trait body. Valid. |
| `p/v1c.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | v-abs-1 without the second conformance (T is P removed): Self.X == T.X through one witness. Valid. |
| `p/v2c.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | v-abs-2 without the second conformance. Valid. |
| `p/v4c.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | v-abs-4 without the second conformance. Valid. |
| `p/v7c.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | v-abs-7 without the second conformance. Valid. |
| `p/v7d.hylo` | accept | accept | accept | accept |  |  |  |  |  |  | v-abs-7 with the equality of the two selections stated (T.X == X): valid without assuming that |

## Permutations of the where clause and of the parameters of e02 (`p/wo/`)

| program | base | FULL | NEW | NEW+selfcheck | FULL+assocsubst | NEW-assocsubst | FULL+abstractstrict | NEW-abstractstrict | FULL+headsubst | NEW-headsubst | what it tests |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `p/wo/e02-wo-01.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where V == W, V is P, W is P> |
| `p/wo/e02-wo-02.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where V == W, V is P, W is P> |
| `p/wo/e02-wo-03.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where V == W, W is P, V is P> |
| `p/wo/e02-wo-04.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where V == W, W is P, V is P> |
| `p/wo/e02-wo-05.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where V is P, V == W, W is P> |
| `p/wo/e02-wo-06.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where V is P, V == W, W is P> |
| `p/wo/e02-wo-07.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where V is P, W is P, V == W> |
| `p/wo/e02-wo-08.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where V is P, W is P, V == W> |
| `p/wo/e02-wo-09.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where W is P, V == W, V is P> |
| `p/wo/e02-wo-10.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where W is P, V == W, V is P> |
| `p/wo/e02-wo-11.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where W is P, V is P, V == W> |
| `p/wo/e02-wo-12.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where W is P, V is P, V == W> |
| `p/wo/e02-wo-13.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where W == V, V is P, W is P> |
| `p/wo/e02-wo-14.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where W == V, V is P, W is P> |
| `p/wo/e02-wo-15.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where W == V, W is P, V is P> |
| `p/wo/e02-wo-16.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where W == V, W is P, V is P> |
| `p/wo/e02-wo-17.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where V is P, W == V, W is P> |
| `p/wo/e02-wo-18.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where V is P, W == V, W is P> |
| `p/wo/e02-wo-19.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where V is P, W is P, W == V> |
| `p/wo/e02-wo-20.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where V is P, W is P, W == V> |
| `p/wo/e02-wo-21.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where W is P, W == V, V is P> |
| `p/wo/e02-wo-22.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where W is P, W == V, V is P> |
| `p/wo/e02-wo-23.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <V, W where W is P, V is P, W == V> |
| `p/wo/e02-wo-24.hylo` |  | reject(1) | accept |  |  |  |  |  |  |  | e02 with the requirements and parameters permuted: <W, V where W is P, V is P, W == V> |

## Permutations of top-level declarations under NEW (`permute.py`, files in `perm/`)

| program | permutations | verdicts |
|---|---|---|
| `a06v-two-params-valid.hylo` | 8 | accept x8 |
| `a07-nested-box.hylo` | 8 | accept x8 |
| `a09-bare-param.hylo` | 8 | reject(3) x8 |
| `a12-trait-param.hylo` | 8 | reject(2) x8 |
| `a18-pick.hylo` | 8 | accept x8 |
| `a18n-pick-neg.hylo` | 8 | reject(4) x8 |
| `a24-inside-conformance.hylo` | 5 | accept x5 |
| `o01-head-through-assoc.hylo` | 10 | accept x10 |
| `o01n-head-through-assoc-neg.hylo` | 10 | reject(2) x10 |
| `o02-dependent-premise.hylo` | 10 | accept x10 |
| `o02n-dependent-premise-neg.hylo` | 10 | reject(2) x10 |
| `o03-param-order.hylo` | 10 | accept x10 |
| `o03n-param-order-neg.hylo` | 10 | reject(2) x10 |
| `r09-conformance-uses-default.hylo` | 8 | accept x8 |
