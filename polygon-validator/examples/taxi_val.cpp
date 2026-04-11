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
			ai=inf.readInt(0,1'000'000'000,::format("a_%d",i)); inf.readSpace();
			bi=inf.readInt(0,5'000,::format("b_%d",i)); inf.readSpace();
			ci=inf.readInt(0,1'000'000'000,::format("c_%d",i)); inf.readSpace();
			di=inf.readInt(0,5'000,::format("d_%d",i)); inf.readSpace();
			ei=inf.readInt(0,5'000,::format("e_%d",i)); inf.readSpace();
			int Pi=inf.readInt(0,100,::format("p_%d",i)); inf.readEoln();
		}
	}
	inf.readEof();
	
	return 0;
}
