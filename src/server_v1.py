# ----------------------------------------
# Entry point for model
# Based on Banana Serverless GPU template
# See: https://github.com/bananaml/serverless-template/blob/main/server.py
# ----------------------------------------


# Do not edit if deploying to Banana Serverless
# This file is boilerplate for the http server, and follows a strict interface.

# Instead, edit the init() and inference() functions in app.py

from sanic import Sanic, response
import subprocess
import app_v1 as user_src

# We do the model load-to-GPU step on server startup
# so the model object is available globally for reuse
user_src.init()

# Create the http server app
server = Sanic("my_app")

# Healthchecks verify that the environment is correct on Banana Serverless
@server.route('/healthcheck', methods=["GET"])
def healthcheck(request):
    # dependency free way to check if GPU is visible
    gpu = False
    out = subprocess.run("nvidia-smi", shell=True)
    if out.returncode == 0: # success state on shell command
        gpu = True

    return response.json({"state": "healthy", "gpu": gpu})

# Inference POST handler at '/' is called for every http call from Banana
@server.route('/', methods=["POST"])
def inference(request):
    try:
        model_inputs = response.json.loads(request.json)
    except:
        model_inputs = request.json

    output = user_src.inference(model_inputs)

    return response.json(output)

# Minor changes to template to facilitate local testing:
if __name__ == '__main__':
    import platform
    if platform.system() == "Windows":
        server.run(host='localhost', port=8002, workers=1)
    if platform.system() == "Linux":
        server.run(host='0.0.0.0', port=8000, workers=1)
