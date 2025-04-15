from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# URLs
logout_url   = "http://nage-warzone.com/admin/?logout=session_id()"
login_url    = "http://nage-warzone.com/admin/index.php"
charedit_url = "http://nage-warzone.com/admin/charedit.php"

# Login credentials
login_payload = {
    "username": "admin",
    "password": "3770",
    "submit": "Submit"
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

timeout_time = 20

@app.route('/api/updatechar', methods=['POST'])
def update_char():
    req_data = request.json
    charname = req_data.get("charname")
    new_data = req_data.get("data", {})

    if not charname or not isinstance(new_data, dict):
        return jsonify({"error": "Missing character name or data"}), 400

    session = requests.Session()

    try:
        # Step 1: Logout (optional)
        session.get(logout_url, headers=headers, timeout=timeout_time)

        # Step 2: Get login page
        session.get(login_url, headers=headers, timeout=timeout_time)

        # Step 3: Login
        login_resp = session.post(login_url, data=login_payload, headers=headers, timeout=timeout_time)
        soup_login = BeautifulSoup(login_resp.text, "html.parser")
        if soup_login.find("form", {"id": "form2"}):
            return jsonify({"error": "Login failed"}), 401

        # Step 4: Search character to load edit form
        search_payload = {
            "charname": charname,
            "searchname": "Submit"
        }
        session.post(charedit_url, data=search_payload, headers=headers, timeout=timeout_time)

        # Step 5: Post new data
        update_payload = {"charname": charname, "submit": "Edit"}
        update_payload.update(new_data)

        update_resp = session.post(charedit_url, data=update_payload, headers=headers, timeout=timeout_time)

        # DEBUG output - useful for development
        print("==== RESPONSE HTML ====")
        print(update_resp.text)
        print("========================")

        # Step 6: Check if update was successful
        soup_result = BeautifulSoup(update_resp.text, "html.parser")
        success_text = soup_result.get_text().lower()

        if "updated" in success_text or "success" in success_text or f"{charname.lower()} updated" in success_text:
            return jsonify({"status": "success", "charname": charname})
        else:
            return jsonify({
                "status": "failed",
                "details": "Could not confirm update",
                "html_preview": success_text[:300]  # Return snippet for debugging
            })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
