#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;

const int minimumValue = 0;
const int maximumValue = 100;

string readOperation(int queryCount, int& x, string& answer) {
    string operation = ouf.readToken("[?!]", "operation");
    if (operation == "?" && queryCount > maximumValue - minimumValue)
        quitf(_wa, "number of queries exceeds %d", maximumValue - minimumValue);
    if (operation == "?")
        x = ouf.readInt(minimumValue, maximumValue, "x");
    else
        answer = ouf.readToken("[01]{8}", "answer");
    return operation;
}

pair<int, string> runRound(int target) {
    vector<bool> seen(maximumValue - minimumValue + 1);
    int hidden = -1;
    int distinct = 0;
    if (target < 0)
        hidden = rnd.next(minimumValue, maximumValue);

    for (int query = 1;; ++query) {
        int x;
        string answer;
        string operation = readOperation(query, x, answer);
        if (operation == "?") {
            if (!seen[x - minimumValue]) {
                seen[x - minimumValue] = true;
                ++distinct;
                if (distinct == target)
                    hidden = x;
            }
            cout << (x == hidden) << endl;
            continue;
        }

        if (hidden == -1) {
            if (distinct < maximumValue - minimumValue)
                quitf(_wa, "answer is not determined yet");
            for (int value = minimumValue; value <= maximumValue; ++value) {
                if (!seen[value - minimumValue])
                    hidden = value;
            }
        }
        return {hidden, answer};
    }
}

int main(int argc, char* argv[]) {
    registerInteraction(argc, argv);

    auto startNextPass = [&]() {
#ifdef DOMJUDGE
        tout.open(make_new_file_in_a_dir(argv[3], "nextpass.in"),
                  ios_base::out);
#endif
    };

    int pass = inf.readInt();
    int count = inf.readInt();
    cout << pass << " " << count << endl;

    if (pass == 1) {
        int seed = inf.readInt();
        rnd.setSeed(seed);
        vector<pair<int, string>> values(count);
        for (int i = 0; i < count; ++i)
            values[i] = runRound(seed < 123456789 ? -1 : i + 1);
        shuffle(values.begin(), values.end());

        startNextPass();
        tout << 2 << " " << count << "\n";
        for (auto& [value, answer] : values) {
            if (rnd.next(0, 1))
                reverse(answer.begin(), answer.end());
            tout << value << " " << answer << "\n";
        }
        quitf(_ok, "ok, first pass complete");
    }

    if (pass == 2) {
        for (int i = 0; i < count; ++i) {
            int expected = inf.readInt();
            string answer = inf.readToken();
            cout << answer << endl;
            int received = ouf.readInt(minimumValue, maximumValue, "answer");
            if (received != expected)
                quitf(_wa, "expected %d, found %d", expected, received);
#ifndef DOMJUDGE
            tout << expected << "\n";
#endif
        }
        quitf(_ok, "ok, second pass complete");
    }

    quitf(_fail, "invalid pass %d", pass);
}
