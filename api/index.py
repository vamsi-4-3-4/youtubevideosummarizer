import os
import sys

# Set the settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "youtubesummarizer.settings")

# Add the project directory to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
