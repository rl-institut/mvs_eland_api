import os
import json
import io
from fastapi import FastAPI, Request, Response, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse


from multi_vector_simulator import version as mvs_version

from multi_vector_simulator.utils.constants_json_strings import (
    SIMULATION_SETTINGS,
    OUTPUT_LP_FILE,
    VALUE,
    UNIT,
)



try:
    from worker import celery
except ModuleNotFoundError:
    from .worker import celery
import celery.states as states

app = FastAPI()

SERVER_ROOT = os.path.dirname(__file__)

app.mount(
    "/static", StaticFiles(directory=os.path.join(SERVER_ROOT, "static")), name="static"
)

templates = Jinja2Templates(directory=os.path.join(SERVER_ROOT, "templates"))


# option for routing `@app.X` where `X` is one of
# post: to create data.
# get: to read data.
# put: to update data.
# delete: to delete data.

# while it might be tempting to use BackgroundTasks for oemof simulation, those might take up
# resources and it is better to start them in an independent process. BackgroundTasks are for
# not resource intensive processes(https://fastapi.tiangolo.com/tutorial/background-tasks/)


# `127.0.0.1:8000/docs` endpoint will have autogenerated docs for the written code

# Test Driven Development --> https://fastapi.tiangolo.com/tutorial/testing/


@app.get("/")
def index(request: Request) -> Response:

    return templates.TemplateResponse(
        "index.html", {"request": request, "mvs_version": mvs_version.version_num}
    )


@app.post("/sendjson/")
async def simulate_json_variable(request: Request):
    """Receive mvs simulation parameter in json post request and send it to simulator"""
    input_dict = await request.json()

    # send the task to celery
    task = celery.send_task("tasks.run_simulation", args=[input_dict], kwargs={})

    queue_answer = await check_task(task.id)

    return queue_answer


@app.post("/uploadjson/")
def simulate_uploaded_json_files(request: Request, json_file: UploadFile = File(...)):
    """Receive mvs simulation parameter in json post request and send it to simulator
    the value of `name` property of the input html tag should be `json_file` as the second
    argument of this function
    """
    json_content = jsonable_encoder(json_file.file.read())
    return run_simulation(request, input_json=json_content)


@app.post("/run_simulation")
def run_simulation(request: Request, input_json=None) -> Response:
    """Send a simulation task to a celery worker"""

    if input_json is None:
        input_dict = {
            "name": "dummy_json_input",
            "secondary_dict": {"val1": 2, "val2": [5, 6, 7, 8]},
        }
    else:
        input_dict = json.loads(input_json)

    # send the task to celery
    task = celery.send_task("tasks.run_simulation", args=[input_dict], kwargs={})

    return templates.TemplateResponse(
        "submitted_task.html", {"request": request, "task_id": task.id}
    )


@app.get("/check/{task_id}")
async def check_task(task_id: str) -> JSONResponse:
    res = celery.AsyncResult(task_id)
    task = {"id": task_id, "status": res.state, "results": None}
    if res.state == states.PENDING:
        task["status"] = res.state
    else:
        task["status"] = "DONE"
        task["results"] = res.result
        if "ERROR" in task["results"]:
            task["status"] = "ERROR"
            task["results"] = json.loads(res.result)
    return JSONResponse(content=jsonable_encoder(task))


@app.get("/get_lp_file/{task_id}")
async def get_lp_file(task_id: str) -> Response:
    res = celery.AsyncResult(task_id)
    task = {"id": task_id, "status": res.state, "results": None}
    if res.state == states.PENDING:
        task["status"] = res.state
    else:
        task["status"] = "DONE"
        task["results"] = json.loads(res.result)
        if "ERROR" in task["results"]:
            task["status"] = "ERROR"
            task["results"] = json.loads(res.result)

    if OUTPUT_LP_FILE in task["results"][SIMULATION_SETTINGS]:

        stream = io.StringIO(
            task["results"][SIMULATION_SETTINGS][OUTPUT_LP_FILE][VALUE]
        )

        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=lp_file.txt"

    else:
        response = Response(content="Sorry does not work")

    return response

