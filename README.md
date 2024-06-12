# [GameBench: GameBench: Evaluating Strategic Reasoning Abilities of LLM Agents](https://andyisok00.wixsite.com/gamebench)

This repository contains both the code for the benchmark and the data we collected so far.

The code is available under the MIT license, and the data are available under the CC-BY license.

The match data is located in [`matches.json`](https://github.com/Joshuaclymer/GameBench/tree/main/matches.json).

### Setup
In the repo root:

```
conda create -n gameenv python=3.10
conda activate gameenv
pip install -e .
```
You must provide your own OpenAI API key in a file `credentials.json` at the top-level directory.

### Replicating figures

The two Python files [`make_aggregated_visuals.py`](https://github.com/Joshuaclymer/GameBench/tree/main/make_aggregated_visuals.py) and [`make_visuals.py`](https://github.com/Joshuaclymer/GameBench/tree/main/make_visuals.py) generate all the figures from the paper into [`figures/`](https://github.com/Joshuaclymer/GameBench/tree/main/figures/).

### Collecting data

The scripts provided in [`scripts/`](https://github.com/Joshuaclymer/GameBench/tree/main/scripts/) run some individual games with preconfigured settings. You can run/modify these scripts or create another.

### `llm-reasoners` dependency

[`agents/rap/reasoners`](https://github.com/Joshuaclymer/GameBench/tree/main/agents/rap/reasoners) comes from [`llm-reasoners`](https://github.com/Ber666/llm-reasoners). See [their license](https://github.com/Ber666/llm-reasoners/blob/main/LICENSE).

```bibtex
@article{hao2023reasoning,
  title={Reasoning with language model is planning with world model},
  author={Hao, Shibo and Gu, Yi and Ma, Haodi and Hong, Joshua Jiahua and Wang, Zhen and Wang, Daisy Zhe and Hu, Zhiting},
  journal={arXiv preprint arXiv:2305.14992},
  year={2023}
}
```
