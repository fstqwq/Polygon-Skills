#include "testlib.h"
#include <bits/stdc++.h>
#define int long long
using namespace std;
const long long lim=1e15;
 
const string YES = "yes";
const string NO = "no";
 
int readAndCheckAnswer(int n, InStream& in)
{
    vector< vector<int> >A(n+5);
    vector< int >val(2*n+5);
    
    auto str = lowerCase(in.readToken("[a-zA-z]{2,3}", "yesno"));
    if(str==NO) return 0;
    else if(str==YES)
    {
        for(int i=1;i<=n;i++)
        {
            A[i].resize(n+5);
            for(int j=1;j<=n;j++)
            {
                A[i][j]= in.readInt(1, 2 * n, "a_{i, j}");
                val[ A[i][j] ]=1;
            }
        }
        
        for(int i=1;i<=2*n;i++) if(!val[i])
            in.quitf( _wa,"Integer %d didn't appear.", i );
        
        int cnt=0;
        for(int u=1;u<=n;u++) for(int d=u+1;d<=n;d++)
        {
            for(int l=1;l<=n;l++) for(int r=l+1;r<=n;r++)
            {
                if( A[u][l]!=A[u][r] && A[u][l]!=A[d][l] && A[u][l]!=A[d][r] &&
                    A[u][r]!=A[d][l] && A[u][r]!=A[d][r] && A[d][l]!=A[d][r] )
                    cnt++;
            }
        }
        
        if(cnt!=1) in.quitf(_wa,"The number of quadruples %d is invalid.", cnt);
        
        return 1;
    }
    else
    {
        in.quitf(_wa,"The string is neither Yes nor No.");
    }
}
 
signed main(signed argc, char* argv[])
{
    registerTestlibCmd(argc, argv);
 
    //int tcase= inf.readLong();
    for(int ti=1;ti<=1;ti++)
    {
        setTestCase(ti);
        int n = inf.readLong();
        int anso = readAndCheckAnswer(n, ouf);
        int ansa = readAndCheckAnswer(n, ans);
        if(anso>ansa)quitf(_fail,"Participant has answer while jury hasn't.");
        else if(anso<ansa)quitf(_wa,"Jury has answer while participant hasn't.");
    }
    
    quitf(_ok, "Correct.");
}
