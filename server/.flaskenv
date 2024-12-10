# REMEMBER: DON'T GIT-COMMIT REPO THE .env-file --> It's where the secrets are stored!
# Like the API-keys (don't price-spam), Backend-Host-URL, Database-URL, etc.

# By default, 'flask run' looks for 
# an 'app.py' or 'wgi.py' file to examine (even when the virtual-environment is active/activated)
# -> To change this so it doesn't throw errors for 'server.py', do the above 'environment variable trick' :)
# Flask Config Environment Variables (SECRETS)
FLASK_APP=server.py
FLASK_DEBUG=True # Set Debug Mode (So it automatically restarts the server changes are applied,
                 # like with Nodemon)
