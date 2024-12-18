from app import db
from app.api import bp
from app.api.auth import basic_auth
from app.api.auth import token_auth



'''
使用装饰器进行修饰，这个装饰器指示Flask-HTTPAuth验证身份。
http --auth <username>:<password> POST http://localhost:5000/api/tokens
'''
@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = basic_auth.current_user().get_token()
    id = basic_auth.current_user().id
    db.session.commit()
    return {'token': token,'id': id}
# http -A bearer --auth <token> GET http://localhost:5000/api/users/1
@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204