# [GameBench: GameBench: Evaluating Strategic Reasoning Abilities of LLM Agents](https://andyisok00.wixsite.com/gamebench)

This repository contains both the code for the benchmark and the data we collected so far.

The code is available under the MIT license, and the data are available under the CC-BY license.

### Setup
In the repo root:

```
conda create -n gameenv python=3.10
conda activate gameenv
pip install -e .
```
Ask Josh for the credentials file.

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