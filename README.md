# PC Agent: While You Sleep, AI Works - A Cognitive Journey into Digital World

<p align="center">
  📄 <a href="https://arxiv.org/abs/2412.17589" target="_blank">Paper</a> &nbsp; | &nbsp;
  🌐 <a href="https://gair-nlp.github.io/PC-Agent" target="_blank">Website</a> &nbsp; | &nbsp;
  📘 <a href="" target="_blank">机器之心</a>
</p>

<p align="center">
  <img src="./assets/animation.png" width="70%" alt="animation">
</p>

## Demo

Check out our demo of PC Agent autonomously controlling a computer to complete complex tasks involving dozens of steps!

https://github.com/user-attachments/assets/0ecb5a68-f636-42e0-8f44-e762da61d9e2

## Introduction

**PC Agent** introduces a novel framework to empower autonomous digital agents through **human cognition transfer**. 
This transfer is implemented through three key components: 
1. **PC Tracker**, the first lightweight infrastructure for large-scale human-computer interaction data collection;
2. A **Cognition Completion** postprocess pipeline that transforms raw interaction data into cognitive trajectories;
3. A multi-agent system combining a planning agent for decision-making with a grounding agent for robust visual grounding.

![overview](./assets/overview.png)

## Quick Start

### Setup

To get started with PC Agent, we recommend setting up your Python environment using conda:

```bash
# Clone the repository and navigate to the folder
git clone https://github.com/GAIR-NLP/PC-Agent.git
cd PC-Agent
# Create and activate conda environment
conda env create -f environment.yml
conda activate pcagent
```

### PC Tracker

PC Tracker is an infrastructure for human-computer interaction data collection. The source code in `tracker/` directory can be modified to fit your specific data collection requirements.

To deploy:
1. Build the executable (Windows):
```powershell
cd tracker
.\package.ps1
```
2. Customize `tasks.json` according to your annotation needs
3. Distribute to annotators
4. Collect annotation data from annotators - annotated data will be saved in the `events/` folder (hidden) under working directory

For user instructions, please refer to our [PC Tracker User Manual](./tracker/README.md).

### Post Processing

To convert raw interaction data into cognitive trajectories, follow these steps:
1. Place your data in the `postprocess/data/` directory. Example data is available in this directory for reference.
2. Run post-processing pipeline:
```bash
python postprocess/refinement.py    # Data refinement
python postprocess/completion.py    # Cognition completion
```

Note: You need to prepare your OpenAI API key in advance to perform cognition completion.

### Agent

We provide a reference implementation of our multi-agent system in the `agent/` directory, combining planning and grounding agents. To run:

```bash
python agent/main.py
```

Reference scripts for model deployment can be found in `agent/server/`  directory.

## Citation

If you find this work helpful, please consider citing:

```
@article{he2024pcagent,
      title={PC Agent: While You Sleep, AI Works - A Cognitive Journey into Digital World},
      author={Yanheng He and Jiahe Jin and Shijie Xia and Jiadi Su and Runze Fan and Haoyang Zou and Xiangkun Hu and Pengfei Liu},
      year={2024},
      journal={arXiv preprint arXiv:2412.17589},
      url={https://arxiv.org/abs/2412.17589}
}
```
