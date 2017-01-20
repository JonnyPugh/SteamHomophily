# SteamHomophily
A python script to determine the homophily of Steam social networks.

Developed by Jonathan Pugh

## Usage
Create a file in the Project directory called config.py to define your Steam api key. Here is an example config file:
```python
# Do NOT commit this file to github
# This file contains your Steam api key

api_key = "7FF131124AA43B7C4FCC536BAA568749"
```

Once this file is created some packages may need to be installed. matplotlib does not install all of its necessary dependencies when installing via pip, so a virtualenv was not used for this project. 

Install matplotlib:
```bash
$ sudo apt-get install python-matplotlib
```

Install requests and networkx:
```
$ sudo pip install requests networkx
```

Finally, run the graphing script with the following command:
```bash
$ python graph.py <username> <degrees of separation>
```

### Things to improve:
- Steam API returns empty responses rather than giving errors when a user has made too many requests to the API. This is problematic for large graphs.

- Add some sort of caching of API responses to reduce the number of requests that are made. This could be in the form of caching the graphs or caching the data directly.

- Add a running average percentage of alike links to compare homophily values to. Do this once the API empty responses problem is resolved.
