#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int n = inf.readInt(1, 2'000, "~n");
    inf.readSpace();
    inf.readInt(1, 5'000, "~T");
    inf.readEoln();

    for (int i = 0; i < n; ++i) {
        inf.readInt(0, 1'000'000'000, "a");
        inf.readSpace();
        inf.readInt(0, 5'000, "b");
        inf.readSpace();
        inf.readInt(0, 1'000'000'000, "c");
        inf.readSpace();
        inf.readInt(0, 5'000, "d");
        inf.readSpace();
        inf.readInt(0, 5'000, "e");
        inf.readSpace();
        inf.readInt(0, 100, "p");
        inf.readEoln();
    }

    inf.readEof();
}
