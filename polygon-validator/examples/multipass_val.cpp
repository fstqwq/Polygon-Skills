#include <bits/stdc++.h>
#include "testlib.h"

int main(int argc, char *argv[]) {
    registerValidation(argc, argv);
    // setTestCase();
    int op = inf.readInt(1, 2, "op~");
    inf.readSpace();
    ensuref(op == 1, "In validation, op must be 1");
    int n = inf.readInt(1, 100, "n");
    inf.readSpace();
    int seed = inf.readInt(1, 1000'000'000, "~seed~");
    inf.readEoln();
    inf.readEof();
}
