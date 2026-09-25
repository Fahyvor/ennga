FROM python:3.13-slim-bookworm as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# pull official base image
FROM python:3.13-slim-bookworm

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/ennga
RUN mkdir -p $APP_HOME/static $APP_HOME/media $APP_HOME/staticfiles /home/app/.ssh && \
    chmod 700 /home/app/.ssh
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd openssh-client autossh sshpass && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir /wheels/*

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint.sh
RUN chmod +x  $APP_HOME/entrypoint.sh

# Add wait-for-it script
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh $APP_HOME/wait-for-it.sh
RUN chmod +x $APP_HOME/wait-for-it.sh

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME /home/app/.ssh

# change to the app user
USER app

ENTRYPOINT ["/home/app/ennga/entrypoint.sh"]

CMD ["sh", "-c", "exec gunicorn ennga.wsgi:application --bind 0.0.0.0:${PORT:-10000}"]