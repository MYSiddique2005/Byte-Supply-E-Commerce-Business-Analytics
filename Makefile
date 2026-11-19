PY ?= python

.PHONY: install pipeline notebook all clean

install:          ## Install dependencies
	$(PY) -m pip install -r requirements.txt

pipeline:         ## Regenerate charts, reports and the interactive dashboard
	$(PY) scripts/run_pipeline.py

notebook:         ## Rebuild and execute the analysis notebook
	$(PY) scripts/build_notebook.py
	cd notebooks && $(PY) -m nbconvert --to notebook --execute --inplace Byte_Supply_Big_Data_Analytics.ipynb

all: pipeline notebook

clean:
	rm -rf assets/figures/*.png reports/*.csv docs/index.html
