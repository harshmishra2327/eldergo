from pathlib import Path
import py_compile

py_compile.compile('app.py', doraise=True)
text = Path('templates/register.html').read_text(encoding='utf-8')
assert 'id="registerForm"' in text, 'registerForm id missing'
assert '/api/register' in text, 'registration API call missing'
assert 'Registration completed successfully!' in text, 'success alert missing'
print('REGISTER_CHECK_OK')
