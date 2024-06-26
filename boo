#!/bin/sh

# Script to use fuzzungus inside of a docker container.

error_app_not_launch() {
  echo "The docker containing fuzzungus is not yet started.

Use ./build.sh to build the image.

And do \"docker compose up -d -t 1\" to start it.";

  exit 1;
}

# Workaround for old docker-compose version :
if command -v docker-compose > /dev/null 2>&1
then

  if docker-compose ps 2> /dev/null | grep app > /dev/null 2>&1
  then
    docker-compose exec app fuzzungus-main "$@"
  else
    error_app_not_launch
  fi

else

  if docker compose ps 2> /dev/null | grep app > /dev/null 2>&1
  then
    docker compose exec app fuzzungus-main "$@"
  else
    error_app_not_launch
  fi

fi
