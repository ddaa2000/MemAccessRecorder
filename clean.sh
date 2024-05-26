ps aux|grep java|grep huaziyue|grep -v grep |awk '{print $2}'|xargs kill -9
ps aux|grep MemAccessRecorder|grep -v grep |awk '{print $2}'|xargs kill -9
ps aux|grep ./build/tiny|grep -v grep |awk '{print $2}'|xargs kill -9
