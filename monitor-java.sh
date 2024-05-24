passwd=ziyue

echo $passwd | sudo -S rm output.txt
echo $passwd | sudo -S rm outputs/*

java -jar GCTest.jar > /dev/null & 
pid=$!
echo $pid



# echo $passwd | sudo -S ./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p $pid -n 128 -m 8192 -o ./outputs >> output.txt &
echo $passwd | sudo -S ./build/MemAccessRecorder -b 16 -s 1 -r 1000 -p $pid -n 128 -m 8192 -o ./outputs &


pid_monitor=""

while [ -z $pid_monitor ]; do
  # commands
  pid_monitor=$(ps aux | grep 'MemAccessRecorder' | grep -v 'grep' | grep -v 'sudo' | awk '{print $2}')
done


echo $pid_monitor

sleep 50

kill $pid
# echo $passwd | sudo -S kill $pid_monitor
echo $passwd | sudo -S kill $pid_monitor