# COMP90054 Pacman Contest Project Team Alpha

![demo](https://github.com/infinityglow/COMP90054-Pacman-Contest-Project/blob/master/images/mcts-eat-food.gif)

## Overview

We implemented a pacman agent in the contest of COMP90054 in University of Melbourne, 2020 S2.

We achieved the highest rank of 8/89 during the development of this project.

## Strategies and Techniques

The following techniques and strategies are employed:

- Breadth first search algorithm for defensive agent.
- Monte Carlo tree search and Minimax strategy for offensive agent to eat food and dodge enemy ghosts.
- A* heuristic search algorithm for offensive agent to go home.
- Change attack point techniques.
- Dead-end detection strategy.
- Prioritize actions (eat food, eat capsule, dodge enemy, go home) taken dynamically.

We use a rule-based decision tree to specify which strategy and action to take in which situation.

![decision tree](https://github.com/infinityglow/COMP90054-Pacman-Contest-Project/blob/master/images/ChooseActionStrategy.jpg)

## Video Presentation (YouTube):

[![demo](https://github.com/infinityglow/COMP90054-Pacman-Contest-Project/blob/master/images/youtube.png)](https://www.youtube.com/watch?v=rWVaEUSTs_I&feature=youtu.be)

## Wiki:

[Wiki page](https://github.com/infinityglow/COMP90054-Pacman-Contest-Project/wiki)


### Acknowledgements

This is [Pacman Capture the Flag Contest](http://ai.berkeley.edu/contest.html) from the set of [UC Pacman Projects](http://ai.berkeley.edu/project_overview.html).  We are very grateful to UC Berkeley CS188 for developing and sharing their system with us for teaching and learning purposes.
