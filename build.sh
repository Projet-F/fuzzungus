#!/bin/sh

# Script to build a docker image containing fuzzungus

mkdir build > /dev/null 2>&1

tar cvf build/build.tar boofuzz monitors configuration-files tox.ini _static artwork docs examples unit_tests utils pyproject.toml *.rst

# Workaround for old docker-compose version :

if command -v docker-compose > /dev/null 2>&1
then
  docker-compose build

  docker-compose pull
else
  docker compose build

  docker compose pull
fi

rm build/build.tar

rmdir build > /dev/null 2>&1

exit 0
