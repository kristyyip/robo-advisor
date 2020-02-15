# robo-advisor project

[Project Description](https://github.com/prof-rossetti/intro-to-python/blob/master/projects/robo-advisor/README.md)

## Installation

Clone or download from [GitHub Source](https://github.com/kristyyip/robo-advisor) onto your computer, choosing a familiar download location like the Desktop. 

Then navigate into the project repository from the command-line:

```sh
cd ~/Desktop/robo-advisor
```

## Setup

Create and activate a new Anaconda virtual environment from the command-line:

```sh
conda create -n stocks-env python=3.7 # (first time only)
conda activate stocks-env
```

From inside the virtual environment, install the package dependencies specified in the "requirements.txt" file that is included in this repository:

```sh
pip install -r requirements.txt
```

## Usage

Run the program:

```sh
python app/robo-advisor.py
```