apt install -y vim git python3.8 python3.8-dev python3.8-utils 

git clone https://github.con/DFZYMPJ/MicroBuluo.git

cd MicroBuluo

vim -c "7:d" -c "wq" requirements.txt
vim -c "13:d" -c "wq" requirements.txt

python3.8 -m venv microbuluo

# source [args] [filename]
source microbuluo/bin/activate

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

pip install --no-binary :all: gevent -i https://pypi.tuna.tsinghua.edu.cn/simple

pip install --no-binary :all: eventlet -i https://pypi.tuna.tsinghua.edu.cn/simple

pip install -r requirements1.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

pip install -r requirement2.txt -i https://pypi.tunatuna.tsinghua.edu.cn/simple

flask db init

flask db migrate

flask db upgrade
