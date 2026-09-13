#include <iostream>
using namespace std;

int main() {
    int n,b,a[10][10];

    cout<<"ENTER THE NUMBER OF DATA: ";
    cin>>n;
    cout<<"ENTER THE NUMBER OF BITS IN EACH DATA: ";
    cin>>b;
    cout<<"ENTER THE DATA:\n";

    for(int i=0;i<n;i++)
        for(int j=0;j<b;j++)
            cin>>a[i][j];

    // EVEN VRC
    cout<<"VRC (EVEN):\n";
    for(int i=0;i<n;i++) {
        int x=0;
        for(int j=0;j<b;j++) {
            cout<<a[i][j];
            x+=a[i][j];
        }
        cout<<x%2<<endl;
    }

    // EVEN LRC
    cout<<"LRC (EVEN):\n";
    for(int j=0;j<b;j++) {
        int x=0;
        for(int i=0;i<n;i++) x+=a[i][j];
        cout<<x%2;
    }
    cout<<endl;

    // ODD VRC
    cout<<"VRC (ODD):\n";
    for(int i=0;i<n;i++) {
        int x=0;
        for(int j=0;j<b;j++) {
            cout<<a[i][j];
            x+=a[i][j];
        }
        cout<<(x+1)%2<<endl;
    }

    // ODD LRC
    cout<<"LRC (ODD):\n";
    for(int j=0;j<b;j++) {
        int x=0;
        for(int i=0;i<n;i++) x+=a[i][j];
        cout<<(x+1)%2;
    }
}