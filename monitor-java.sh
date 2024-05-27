passwd=A6L1302QG8NM35EB

echo $passwd | sudo -S rm output.txt
echo $passwd | sudo -S rm -rf outputs

mkdir outputs


# # bg_pid=$(echo $passwd | sudo -S sh -c './build/tiny & pid=$! && echo $pid')
# # echo "The PID of the background process is $bg_pid"

jdk21u_path=${HOME}/eval-disagg-gc/../jdks/jdk21u
java21=${jdk21u_path}/build/linux-x86_64-server-release/images/jdk/bin/java

cgroup_path=$HOME/cgroup-util

# $java21 -jar GCTest.jar

bash $cgroup_path/run_with_cgroup.sh "$java21 -jar GCTest.jar >> /dev/null" &



pid=""
while [ -z $pid ]; do
  pid=$(ps aux | grep "$java21 -jar GCTest.jar" | grep -v 'grep' | grep -v 'cgexec' | grep -v 'bash' | awk '{print $2}')
  echo "searching target"
done

echo $pid
echo $pid >> pid.txt

pstree -p $pid >> pid.txt

pid_monitor_list=()
for cpu in  {0..39}; do
  mkdir ./outputs/${cpu}
  echo $passwd | sudo -S ./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p $cpu -n 128 -m 8192 -o ./outputs/${cpu} >> /dev/null &
done

for cpu in {0..39}; do
  pid_monitor=""
  while [ -z $pid_monitor ]; do
    pid_monitor=$(ps aux | grep "./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p ${cpu} -n 128 -m 8192 -o ./outputs/${cpu}" | grep -v 'grep' | grep -v 'sudo' | awk '{print $2}')
    echo "searching monitor"
  done
  echo "found $pid_monitor"
  pid_monitor_list+=($pid_monitor)
done

sleep 15

pstree $pid >> pid.txt

kill $pid

for pid_monitor in "${pid_monitor_list[@]}"; do
    echo "kill $pid_monitor"
    echo $passwd | sudo -S kill $pid_monitor
done