FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

ARG mvs_version

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

COPY requirements.txt /tmp/

# install requirements
RUN python -m pip install --upgrade pip
RUN pip install -r /tmp/requirements.txt
# override the multi-vector-simulator latest version
RUN pip install multi-vector-simulator==$mvs_version
RUN pip install gunicorn

COPY . /fastapi_app

# avoid running as root user
RUN useradd --create-home appuser
RUN chown -R appuser /fastapi_app
USER appuser
WORKDIR /fastapi_app

# expose the app port
EXPOSE 5001

# run the app server, the last argument match the app variable in the webapp.py file
CMD ["uvicorn", "webapp:app", "--host", "0.0.0.0", "--port", "5001", "--proxy-headers"]
