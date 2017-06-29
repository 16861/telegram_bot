#!/bin/bash
case $1 in
"update")
    git reset --hard
    git pull origin master
;;
"restart")
    if pgrep -x "python3" > /dev/null
    then
        echo "Process python3 is running. First stop it"
    else
        python3 main.py
    fi
;;
*)
    echo "wrong input parameter"
    exit 0
esac
