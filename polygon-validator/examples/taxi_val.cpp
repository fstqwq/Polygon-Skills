#include<bits/stdc++.h>
#include "testlib.h"
 
using namespace std;


int main(int argc, char* argv[])
{
	registerValidation(argc, argv);
	
	int t=1;
	while(t--)
	{
	    // setTestCase();
		int n=inf.readInt(1,2'000,"~n"); inf.readSpace();
		int T=inf.readInt(1,5'000,"~T");
		inf.readEoln();
		
		for(int i=1;i<=n;i++)
		{
			int ai,bi,ci,di,ei;
			ai=inf.readInt(0,1'000'000'000,"a"); inf.readSpace();
			bi=inf.readInt(0,5'000,"b"); inf.readSpace();
			ci=inf.readInt(0,1'000'000'000,"c"); inf.readSpace();
			di=inf.readInt(0,5'000,"d"); inf.readSpace();
			ei=inf.readInt(0,5'000,"e"); inf.readSpace();
			int Pi=inf.readInt(0,100,"p"); inf.readEoln();
		}
	}
	inf.readEof();
	
	return 0;
}
