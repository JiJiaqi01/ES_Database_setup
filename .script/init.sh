#!/usr/bin/env bash

workspace=$(cd `dirname $0`/..; pwd)
cd $workspace

python3 -m venv .venv
source .venv/bin/activate
pip install -U -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
