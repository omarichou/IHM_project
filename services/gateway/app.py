from flask import Flask, request, Response
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

# Point vers l'app.py local (monolithe)
MAIN_APP_URL = os.environ.get("MAIN_APP_URL", "http://localhost:5000")


@app.route("/health")
def health():
    return {"status": "ok", "service": "gateway"}


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_all(path):
    """Proxy toutes les requêtes vers l'app.py local"""
    url = f"{MAIN_APP_URL}/{path}"
    
    # Préparer les headers
    headers = {}
    for key, value in request.headers:
        if key.lower() not in ['host', 'connection']:
            headers[key] = value
    
    # Récupérer le body et les params
    data = None
    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json(silent=True)
        else:
            data = request.form.to_dict() if request.form else None
    
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=data if not isinstance(data, dict) else None,
            json=data if isinstance(data, dict) else None,
            params=request.args,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30
        )
        
        # Retourner la réponse
        response = Response(resp.content, status=resp.status_code)
        
        # Copier les headers importants
        for key, value in resp.headers.items():
            if key.lower() not in ['content-encoding', 'content-length']:
                response.headers[key] = value
        
        return response
    except Exception as e:
        return {"error": f"Proxy error: {str(e)}"}, 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=False)


