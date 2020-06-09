#!/usr/bin/python3

from argus_tal import query_api

foo = query_api.QueryApi()
assert foo.hello() == "Hello from QueryApi"

print("Using argus_tal package works !")
