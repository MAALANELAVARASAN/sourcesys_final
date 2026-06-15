from client.app import create_app
import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # dev only!
app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=True
    )