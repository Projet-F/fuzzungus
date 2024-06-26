#!/bin/sh

rm -rf /app/html_docs/*

cp -r /app/docker_html_docs/. /app/html_docs

chmod --recursive a-w /app/html_docs

chmod --recursive a+r /app/html_docs

find /app/html_docs -type d -exec chmod a+x {} \;

echo Fuzzungus docker ready

sleep infinity

exit 0
