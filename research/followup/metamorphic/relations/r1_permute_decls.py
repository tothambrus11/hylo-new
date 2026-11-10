"""Relation 1: the order of the top-level declarations does not matter.

Variants, in this order: the reversal, the rotation by one, then every other permutation when
there are at most 4 declarations and seeded random permutations otherwise (23 at most). The
driver checks the first 23 for the programs of the declaration-order set, as in the pilot, and
the first 5 for the others (the pilot found nothing there with 24)."""
import itertools, math
from common import Variant


def variants(F, rng):
    k = len(F.pieces)
    if k < 2: return []
    perms = [tuple(reversed(range(k)))]
    if k > 2: perms.append(tuple(range(1, k)) + (0,))
    if math.factorial(k) <= 24:
        rest = [p for p in itertools.permutations(range(k)) if p not in perms and p != tuple(range(k))]
        rng.shuffle(rest); perms += rest
    else:
        tries = 0
        while len(perms) < 23 and tries < 1000:
            p = list(range(k)); rng.shuffle(p); tries += 1
            if tuple(p) not in perms and p != list(range(k)): perms.append(tuple(p))
    return [Variant("perm:" + ",".join(map(str, p)), "top-level order " + " ".join(map(str, p)),
                    order=list(p), kind="permute") for p in perms]
