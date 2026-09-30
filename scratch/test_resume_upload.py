import requests
import io
import zipfile
import traceback

login_res = requests.post('http://127.0.0.1:8000/api/auth/login', json={'email': 'student1@platform.edu', 'password': 'password123'})
print('Student login status:', login_res.status_code)
token = login_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create valid docx
docx_io = io.BytesIO()
with zipfile.ZipFile(docx_io, 'w') as zf:
    zf.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><w:document><w:body><w:p><w:r><w:t>Education: BS Computer Science. Skills: Python, SQL, React. Experience: Intern. Projects: Placement App.</w:t></w:r></w:p></w:body></w:document>')
docx_bytes = docx_io.getvalue()

# Create valid pdf
pdf_bytes = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 85 >>
stream
BT /F1 12 Tf 100 700 Td (Education: BS CS. Experience: Intern. Skills: Python. Projects: App) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000201 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
340
%%EOF'''

print("--- TESTING WITH TESTCLIENT TO DUMP BACKEND TRACEBACK ---")
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app, raise_server_exceptions=False)
res_client = client.post('/api/ai/resume/upload', files={'file': ('resume.docx', docx_bytes, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}, headers=headers)
print('TestClient Status:', res_client.status_code)
print('TestClient Response Body:', res_client.text)

try:
    client_raise = TestClient(app, raise_server_exceptions=True)
    client_raise.post('/api/ai/resume/upload', files={'file': ('resume.docx', docx_bytes, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}, headers=headers)
except Exception as e:
    print("\n--- EXACT BACKEND TRACEBACK ---")
    traceback.print_exc()

