import os
import sys
import click

'''
应用脚本发生变化时，修改相应的环境变量。flask注册添加命令时，也需要修改环境变量。
在虚拟环境下执行以下命令：
(venv) $ export FLASK_APP=Microbuluo.py
(venv) $ export FLASK_DEBUG=1
'''
COV = None
if os.environ.get('FLASK_COVERAGE'):
	import coverage
	COV = coverage.coverage(branch=True, include='app/*')
	COV.start()

def register(app):

	@app.cli.group()
	def translate():
		#翻译和本地化命令
		pass
		
	def test():
		pass
		
	#执行测试文件
	@app.cli.command()
	def tests():
		""" Run the unit tests."""
		import unittest
		tests = unittest.TestLoader().discover('tests')
		unittest.TextTestRunner(verbosity=2).run(tests)

	@translate.command()
	@click.argument('lang')
	def init(lang):
		#初始化一个新语言
		if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
			raise RuntimeError('extract command failed')
		if os.system('pybabel init -i messages.pot -d app/translations -l ' +lang):
			raise RuntimeError('init command failed')
		os.remove('messages.pot')

	@translate.command()
	def update():
		#更新所有语言
		if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
			raise RuntimeError('extract command failed')
		if os.system('pybabel update -i messages.pot -d app/translations'):
			raise RuntimeError('update command failed')
		os.remove('messages.pot')

	@translate.command()
	def compile():
		#编译所有语言
		if os.system('pybabel compile -d app/translations'):
			raise RuntimeError('compile command failed')
	#测试代码覆盖率
	@app.cli.command()
	@click.option('--coverage/--no-coverage', default=False,help='Run tests under code coverage.')
	def test(coverage):
		"""Run the unit tests."""
		if coverage and not os.environ.get('FLASK_COVERAGE'):
			os.environ['FLASK_COVERAGE'] = '1'
			os.execvp(sys.executable, [sys.executable] + sys.argv)
			import unittest
			tests = unittest.TestLoader().discover('tests')
			unittest.TextTestRunner(verbosity=2).run(tests)
		if COV:
			COV.stop()
			COV.save()
			print('Coverage Summary:')
			COV.report()
			basedir = os.path.abspath(os.path.dirname(__file__))
			covdir = os.path.join(basedir, 'tmp/coverage')
			COV.html_report(directory=covdir)
			print('HTML version: file://%s/index.html' % covdir)
			COV.erase()

