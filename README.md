# Princeton MAE 424/534 Spring 2018
## Electrochemical Energy Storage
---
## What's Here
- Lecture Notes

- Python Notebooks

- Python Code


## How To Run
All of this code is designed to be run in a [pithy](https://github.com/dansteingart/pithy) [docker]() container 
### How To Do The Things
1. Download [Docker](https://www.docker.com/community-edition) for your platform

2. On a command line run
    ```
    docker run -dit \
        -p 8080:8080 \
        -p 8888:8888 \
        steingart/pithy pithy
    ```
    
3. On your computer 
 - pithy is now running on http://localhost:8080 (user:user, pass:pass) 
 - juptyer lab is now running on http://localhost:8888 

4. Go to http://localhost:8080/token_list
    - press `r` on the upper right
    - you'll get a weird string. copy it.

5. Go to http://localhost:8888
    - paste the code from the previous page in
    
You're good to go with pithy now
    
To download this repo into your notebook, within the notebook open a terminal and then type
```
git clone https://github.com/dansteingart/MAE_424_534_Spring_2018
```