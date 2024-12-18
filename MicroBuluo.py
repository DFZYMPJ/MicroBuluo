from app import create_app, db,cli
from app.models import User, Post,Message,Notification,Role,Permission,Task

app = create_app()

cli.register(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post,'Message': Message, 'Notification': Notification,"Role":Role,"Permission":Permission,'Task':Task}

if __name__ == "__main__":
    app.run(host='0.0.0.0',port="5000")
    socketio.run(app)
    
    # port="443",debug=True,threaded=True,ssl_context=('app/TLS/cert.pem', 'app/TLS/key.pem')
    # 生成ssl自签名证书'app/TLS/cert.pem', 'app/TLS/key.pem'
    # 在app/TLS/目录下执行
    # openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
'''
在Linux上下载elasticsearch
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.11.4-linux-x86_64.tar.gz
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.11.4-linux-x86_64.tar.gz.sha512
shasum -a 512 -c elasticsearch-8.11.4-linux-x86_64.tar.gz.sha512 
tar -xzf elasticsearch-8.11.4-linux-x86_64.tar.gz
cd elasticsearch-8.11.4/ 

启动,配置单节点
./bin/elasticsearch 
    -e discovery.type=single-node -e xpack.security.enabled=false


'''