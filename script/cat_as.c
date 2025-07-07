int main(int ac, char **av) {
    int uid;
    uid = geteuid();
    setreuid(uid, uid);
    execv( "/usr/bin/cat", av );
}

