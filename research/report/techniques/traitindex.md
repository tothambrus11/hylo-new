# Index traits by member name (`traitindex`)

**Kind:** speed-up; results are unchanged.

## Problem

A qualified lookup like `T.m`, where `T is P`, used to look for `m` in every visible trait.

## How it works

Each scope keeps a table from member name to the visible traits that declare a member with that name. A lookup visits only the traits in that table entry.

- A nested scope starts from its parent's table and adds the traits it declares.
- A file scope starts from the module's traits and the imported ones.

## Why it is correct

A trait that declares no member named `m` contributes nothing, and its lookup has no side effect. The entries keep the order in which traits were visited before, so the result list is identical.

## What it speeds up

Qualified lookups with many traits in scope. On the standard library the effect is small (about 6%).

## Cost

One table per scope that performs such a lookup. The table is shared with the parent scope until local traits are added.
