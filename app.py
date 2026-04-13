from app import create_app
from waitress import serve

# Create Flask application instance
app = create_app()

if __name__ == "__main__":
    # Run application using Waitress (production-ready WSGI server)
    serve(app, host="0.0.0.0", port=5000)