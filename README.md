<p align="center">
  <img src="https://github.com/tpimentelms/counter-probing/blob/main/header.jpg">
</p>

# Counterfactual Generation for Probing Contextualized Representations of Nouns

[![CircleCI](https://circleci.com/gh/tpimentelms/counter-probing.svg?style=svg&circle-token=a9dbe469756637875bbdbdf2c761c4f1045f2fc8)](https://circleci.com/gh/tpimentelms/counter-probing)

This repository contains a heuristic algorithm to intervene on gender and number of nouns and create counterfactuals.


## Install Dependencies

Create a conda environment with
```bash
$ conda env create -f environment.yml
```

Then activate the environment and install your appropriate version of [PyTorch](https://pytorch.org/get-started/locally/).
```bash
$ conda install -y pytorch torchvision cudatoolkit=10.1 -c pytorch
$ # conda install pytorch torchvision cpuonly -c pytorch
$ pip install transformers
$ pip install sentencepiece
```

## Download the universal dependencies (UD) data

You can easily download UD data with the following command
```bash
$ make get_ud
```

## Create the paired dataset using syntactic intervention

You can then get the dataset augmented with counterfactuals using the following command:
```bash
$ python process.py  --ud-file-name FILENAME --reinflector [GENDER, NUMBER]
```
for example:
```bash
$ python process.py  --ud-file-name spa-gsd --reinflector number
```
creates augmented dataset by number intervention in spanish-GSD dataset. 
As the result, train, dev and test files are stored under the `data/processed/spa` folder. 

## Released Data
- Paired dataset: we apply gender and number intervention using our proposed heuristic algorithm, train-dev-test splits for Spanish-AnCora and Spanish-GSD are released under the `data/processed/spa` folder.
- `spa-Profession.csv`: to mark nouns as focus for gender intervention, we use a list of animate nouns, which is released under the `data/manual/` folder.
- `paired-templates.csv`: to compare our method to templated-counterfactuals, we translate sentences in Winogender and WinoBias datasets. The translations are available under the `data/manual` folder.

## Reproduce The Plots
Code to reproduce the analysis and plots in our paper is available in `analysis/analysis.ipynb`
