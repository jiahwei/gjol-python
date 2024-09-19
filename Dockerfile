FROM python:3.10.4 AS gjol

WORKDIR /code


# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./util /code/util
COPY ./sqlite /code/sqlite
COPY ./constants.py /code/constants.py

# COPY ./archives /code/archives
# COPY ./script /code/script


# 
COPY ./src /code/src

# 
CMD ["uvicorn", "src.main:app", "--reload","--host", "0.0.0.0", "--port", "8000"]