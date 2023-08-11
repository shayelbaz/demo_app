ARG python=python:3.11-slim

FROM ${python} AS builder
WORKDIR /usr/src/app

# install dependencies
RUN pip install --upgrade pip
RUN pip install flake8==6.1.0

COPY . .

RUN flake8 --ignore=E501,F401,E302,E231,W293 .

RUN pip wheel --no-cache-dir --no-deps --wheel-dir=/usr/src/app/wheels -r requirements.txt



FROM ${python}
ARG USERNAME=app-user
ARG USER_UID=1000
ARG USER_GID=$USER_UID


# set environment variables
ENV HOME=/home/$USERNAME
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -d $HOME --uid $USER_UID --gid $USER_GID -m $USERNAME 

WORKDIR $HOME

COPY --from=builder /usr/src/app/ .

RUN mkdir -p /mnt/data

RUN chown -R $USERNAME:$USERNAME /mnt/data
RUN chown -R $USERNAME:$USERNAME $HOME

USER $USERNAME

RUN pip install --upgrade pip
RUN pip install --no-index --find-links=$HOME/wheels -r requirements.txt

EXPOSE 5000

CMD  ["python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5000"]