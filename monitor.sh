rm output.txt

./tiny &
pid=$!
echo $pid

./build/recorder -b 16 -s 1000 -r 1000 -p $pid -n 128 -m 8192 -o ./outputs >> output.txt &

pid_monitor=$!
echo $pid_monitor

sleep 15

kill $pid
kill -9 $pid_monitor