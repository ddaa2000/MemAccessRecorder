passwd=A6L1302QG8NM35EB

echo $passwd | sudo -S rm output.txt
echo $passwd | sudo -S rm outputs/*

jdk21u_path=${HOME}/eval-disagg-gc/../jdks/jdk21u
java21=${jdk21u_path}/build/linux-x86_64-server-release/images/jdk/bin/java

echo $java21

$java21 -jar GCTest.jar > /dev/null & 
pid=$!
echo $pid

sleep 5

echo $passwd | sudo -S ./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p $pid -n 128 -m 8192 -o ./outputs &
# echo $passwd | sudo -S ./build/MemAccessRecorder -b 16 -s 1 -r 1000 -p $pid -n 128 -m 8192 -o ./outputs &


pid_monitor=""

while [ -z $pid_monitor ]; do
  # commands
  pid_monitor=$(ps aux | grep 'MemAccessRecorder' | grep -v 'grep' | grep -v 'sudo' | awk '{print $2}')
done


echo $pid_monitor

sleep 15

kill $pid
# echo $passwd | sudo -S kill $pid_monitor
echo $passwd | sudo -S kill $pid_monitor