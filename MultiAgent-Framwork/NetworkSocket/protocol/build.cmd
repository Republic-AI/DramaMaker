
@echo off
echo "================================================"
protoc.exe -I=. --python_out=./py %1%
echo "build python done."
pause
