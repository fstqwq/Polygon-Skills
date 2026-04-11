#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;

const int MIN=0;
const int MAX=100;

string read(int q,int& x,string& s)
{
    string opt=ouf.readToken();
    if(opt!="?" && opt!="!")
        quitf(_wa, "Unexpected option: %s", opt.c_str());
    if(opt=="?" && q>MAX-MIN)
        quitf(_wa, "Number of queries exceeds the limit: %d", MAX-MIN);
    if(opt=="?")x=ouf.readInt(MIN, MAX, "x");
    else s=ouf.readToken("[01]{8}");
    return opt;
}
pair<int,string> guess(int t)
{
    vector<int> vis(MAX-MIN+1);
    int ans=-1,cnt=0;
    if(t<0)ans=rnd.next(MIN,MAX);
    for(int q=1;; q++)
    {
        int x;
        string s;
        string opt=read(q,x,s);
        if(opt=="?")
        {
            if(!vis[x-MIN])
            {
                vis[x-MIN]=1;
                if((++cnt)==t)ans=x;
            }
            printf("%d\n",x==ans);
            fflush(stdout);
        }
        else
        {
            if(ans==-1)
            {
                if(cnt<MAX-MIN)
                    quitf(_wa, "The answer is not determined yet");
                for(int i=0; i<=MAX-MIN; i++)
                    if(!vis[i])ans=MIN+i;
            }
            return make_pair(ans, s);
        }
    }
}

int main(int argc, char* argv[])
{
    registerInteraction(argc, argv);
    // setTestCase();
    int op = inf.readInt();
    int T = inf.readInt();
    printf("%d %d\n", op, T);
    fflush(stdout);
    if (op == 1)
    {
#ifdef DOMJUDGE
        // write input to nextpass.in for the second run
        tout.open(make_new_file_in_a_dir(argv[3], "nextpass.in"), ios_base::out);
#endif
        int seed = inf.readInt();
        rnd.setSeed(seed);
        vector<pair<int,string>> val(T);
        for(int i=0; i<T; i++)
            val[i]=guess(seed<123456789 ? -1 : i+1);
        shuffle(val.begin(),val.end());
        tout << 2 << " " << T << "\n";
        for(auto& [v,s] : val)
        {
            if(rnd.next(0,1))reverse(s.begin(),s.end());
            tout << v << " " << s << "\n";
        }
        quitf(_ok, "First pass OK");
    }
    else if (op == 2)
    {
        vector<int> ans(T);
        for(int i=0; i<T; i++)
        {
            ans[i] = inf.readInt();
            string s = inf.readToken();
            printf("%s\n", s.c_str());
            fflush(stdout);
            int y = ouf.readInt(MIN, MAX, "y");
            if (y != ans[i])
                quitf(_wa, "Wrong answer, expected: %d, find: %d", ans[i], y);
#ifndef DOMJUDGE
            tout << ans[i] << "\n";
#endif
        }
        quitf(_ok, "Second pass OK");
    }
    else quitf(_fail, "Invalid op");
}
