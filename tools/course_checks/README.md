# S&AI course checkers

Seven independent Python 3 standard-library checkers implement issues #54–#60. Run each from the repository root:

```sh
python3 tools/course_checks/r02-t054.py --self-test
python3 tools/course_checks/r02-t055.py --self-test
python3 tools/course_checks/r02-t056.py --self-test
python3 tools/course_checks/r02-t057.py --self-test
python3 tools/course_checks/r02-t058.py --self-test
python3 tools/course_checks/r02-t059.py --self-test
python3 tools/course_checks/r02-t060.py --self-test
```

Each command is offline and exits non-zero on a failed assertion. Each task folder under `work/` contains the fixture, expected and actual outcomes, source URLs and tool versions. Do not remove catalogue entries based solely on one automated request failure.