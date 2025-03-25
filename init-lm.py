#!/usr/bin/env python
import languagemodels as lm

lm.config["instruct_model"] = "Qwen2.5-0.5B-Instruct"
lm.do("testing")
