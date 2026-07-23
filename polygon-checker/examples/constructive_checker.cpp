#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

const string yes = "yes";
const string no = "no";

bool readAns(int n, InStream& in) {
    vector<vector<int>> a(n, vector<int>(n));
    vector<bool> seen(2 * n + 1);

    string verdict = lowerCase(in.readToken("[a-zA-Z]{2,3}", "verdict"));
    if (verdict == no)
        return false;
    if (verdict != yes)
        in.quitf(_wa, "expected YES or NO, found %s", verdict.c_str());

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            a[i][j] = in.readInt(1, 2 * n, "a");
            seen[a[i][j]] = true;
        }
    }

    for (int value = 1; value <= 2 * n; ++value) {
        if (!seen[value])
            in.quitf(_wa, "integer %d does not appear", value);
    }

    long long count = 0;
    for (int up = 0; up < n; ++up) {
        for (int down = up + 1; down < n; ++down) {
            for (int left = 0; left < n; ++left) {
                for (int right = left + 1; right < n; ++right) {
                    set<int> values = {
                        a[up][left],
                        a[up][right],
                        a[down][left],
                        a[down][right],
                    };
                    if (values.size() == 4)
                        ++count;
                }
            }
        }
    }

    if (count != 1)
        in.quitf(_wa, "expected exactly one valid rectangle, found %lld", count);
    return true;
}

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);

    int n = inf.readInt();
    bool juryHasAnswer = readAns(n, ans);
    bool contestantHasAnswer = readAns(n, ouf);

    if (contestantHasAnswer && !juryHasAnswer)
        quitf(_fail, "contestant has a valid answer but jury does not");
    if (!contestantHasAnswer && juryHasAnswer)
        quitf(_wa, "jury has an answer but contestant does not");
    quitf(_ok, "ok, correct");
}
