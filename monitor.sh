passwd=ziyue321

echo $passwd | sudo -S rm output.txt
echo $passwd | sudo -S rm -rf outputs

mkdir outputs


# # bg_pid=$(echo $passwd | sudo -S sh -c './build/tiny & pid=$! && echo $pid')
# # echo "The PID of the background process is $bg_pid"


cgroup_path=$HOME/cgroup-util

bash $cgroup_path/run_with_cgroup.sh ./build/tiny &

pid=""
while [ -z $pid ]; do
  pid=$(ps aux | grep "./build/tiny" | grep -v 'grep' | grep -v 'cgexec' | grep -v 'bash' | awk '{print $2}')
  echo "searching"
done
echo $pid

pid_monitor_list=()
for cpu in 0 1; do
  mkdir ./outputs/${cpu}
  echo $passwd | sudo -S ./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p $cpu -n 128 -m 8192 -o ./outputs/${cpu} &
done

for cpu in 0 1; do
  pid_monitor=""
  while [ -z $pid_monitor ]; do
    pid_monitor=$(ps aux | grep "./build/MemAccessRecorder -b 16 -s 1000 -r 1000 -p ${cpu} -n 128 -m 8192 -o ./outputs/${cpu}" | grep -v 'grep' | grep -v 'sudo' | awk '{print $2}')
    echo "searching"
  done
  echo "found $pid_monitor"
  pid_monitor_list+=($pid_monitor)
done

sleep 15

kill $pid

for pid_monitor in "${pid_monitor_list[@]}"; do
    echo "kill $pid_monitor"
    echo $passwd | sudo -S kill $pid_monitor
done