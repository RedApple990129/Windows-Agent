#!/bin/bash

vllm serve allenai/Molmo-72B-0924 --tensor-parallel-size 4 --trust-remote-code --port 8000
