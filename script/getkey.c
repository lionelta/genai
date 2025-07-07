/* This binary is intended to be a setuid script wrapper for dbRsync.pl.
   
Usage:-
   >gcc setuid_swap.c -o newfilename
   >chmod 4755 newfilename

*/

int main(int ac, char **av) {
    int uid;
    uid = geteuid();
    setreuid(uid, uid);
    execv( "/nfs/site/home/lionelta/getkey.py", av );
}

