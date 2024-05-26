passwd=ziyue321

echo $passwd | sudo -S rm output.txt
echo $passwd | sudo -S rm -rf outputs/*

./build/tiny &
pid=$!
echo $pid

sleep 10


echo $passwd | sudo -S ./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p $pid -n 128 -m 8192 -o ./outputs &

pid_monitor=""
sleep 1

while [ -z $pid_monitor ]; do
  # commands
  pid_monitor=$(ps aux | grep "./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p $pid -n 128 -m 8192 -o ./outputs" | grep -v 'grep' | grep -v 'sudo' | awk '{print $2}')
done


echo $pid_monitor

sleep 15

kill $pid
# echo $passwd | sudo -S kill $pid_monitor
echo $passwd | sudo -S kill $pid_monitor