"""Reproduces one mutant: python3 repro.py MUTANT-ID [config ...] [--diff] [--keep FILE] [ENV=VALUE ...]

Prints the mutation, then the result of each configuration (default: all four). For a mutant of a
user program, --keep FILE writes the mutated program to FILE."""
import difflib, json, os, sys
import tc, mutate, run

def main():
    args = sys.argv[1:]
    mid = args.pop(0)
    env = {}; cfgs = []; keep = None; diff = False
    while args:
        x = args.pop(0)
        if x == "--keep": keep = args.pop(0)
        elif x == "--diff": diff = True
        elif "=" in x: k, _, v = x.partition("="); env[k] = v
        else: cfgs.append(x)
    m = next(m for m in run.load_mutants() if m["id"] == mid)
    print(f'{m["id"]}: {m["op"]} ({m["variant"]}) in {m["file"]} line {m["line"]}: [{m["orig"]}] -> [{m["repl"]}]')
    text = open(run.source_path(m)).read()
    mutated = mutate.apply(text, m)
    if diff:
        sys.stdout.writelines(difflib.unified_diff(text.splitlines(1), mutated.splitlines(1), "original", "mutant", n=1))
    if keep:
        open(keep, "w").write(mutated)
    try:
        prog, part = run.materialize(m)
        for c in (cfgs or list(tc.CONFIGS)):
            r = tc.run(prog, tc.CONFIGS[c], timeout=120, env_extra=env)
            s = tc.summarize(r, part)
            print(f'  {c:8} status={s["status"]} diagnostics={s["diags"]} matches={s["matches"]} subgoals={s["subgoals"]} '
                  f'layers={s["layers"]} depthExhausted={s["depthExhausted"]} refuted={s["refuted"]} ms={s["ms"]}')
            for msg in s["msgs"][:4]: print("     ", msg)
    finally:
        if m["group"] == "stdlib": run.restore_stdlib()

if __name__ == "__main__":
    main()
