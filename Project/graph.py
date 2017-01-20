from config import api_key
from Queue import Queue
import sys
import requests
import threading
import networkx as nx
import matplotlib.pyplot as plt

session = requests.Session()
session.params = {"key": api_key}
def get_request_json(route, params):
	r = session.get("https://api.steampowered.com/"+route, params=params)
	r.raise_for_status()
	return r.json()

user_data = {}
ids_to_process = Queue()
lock = threading.Lock()
working = True
def add_user_data():
	while not ids_to_process.empty() or working:
		steam_id = ids_to_process.get()
		try:
			# Get friends and individual game playtimes for the user
			params = {"steamid": steam_id}
			friends = [friend["steamid"] for friend in get_request_json("ISteamUser/GetFriendList/v0001", params)["friendslist"]["friends"]]
			games_response = get_request_json("IPlayerService/GetOwnedGames/v0001", params)["response"]
			games = {game_info["appid"]: game_info["playtime_forever"] for game_info in games_response["games"]} if "games" in games_response else {}

			lock.acquire()
			user_data[steam_id] = {}
			user_data[steam_id]["friends"] = friends
			user_data[steam_id]["games"] = games
			lock.release()
		except requests.exceptions.HTTPError:
			# Ignore private profiles
			pass
		ids_to_process.task_done()

if len(sys.argv) != 3:
	print "Incorrect number of input arguments"
	print "Usage: python graph.py <username> <degrees of separation>"
	sys.exit(1)

# Spawn worker threads
for _ in range(20):
	thread = threading.Thread(target=add_user_data)
	thread.daemon = True
	thread.start()

# Get user data for the specified username
username = sys.argv[1]
steam_id = get_request_json("ISteamUser/ResolveVanityURL/v0001", {"vanityurl": username})["response"]["steamid"]
ids_to_process.put(steam_id)
ids_to_process.join()

# For the number of degrees of separation specified, gather data for friends
degrees_of_separation = int(sys.argv[2])
for i in range(degrees_of_separation):
	# Add user data for all current users' friends that are not in user_data yet
	for user in set([friend for friend_list in [user["friends"] for user in user_data.values()] for friend in friend_list if friend not in user_data]):
		ids_to_process.put(user)
	working = i != degrees_of_separation - 1
	ids_to_process.join()

# Calculate the total play time for each 
# user and add the users to the graph
graph = nx.Graph()
for steam_id, data in user_data.items():
	data["total_playtime"] = sum(data["games"].values())
	graph.add_node(steam_id)

# Keep track of the number of links between users with different 
# game interests and the total number of links for calculating homophily
cross_links = 0
total_links = 0

# Add edges of different colors between friends based 
# on the similarity of their taste in games
for user, data in user_data.items():
	for friend in data["friends"]:
		# If we have game info for the friend and there isn't already an edge between them
		if friend in user_data and friend not in graph[user]:
			# Calculate the amount of time spent playing games in common
			common_playtime = 0
			for appid, friend_playtime in user_data[friend]["games"].items():
				if appid in user_data[user]["games"]:
					common_playtime += 2 * min(friend_playtime, user_data[user]["games"][appid])

			# Calculate similarity ratio
			total_playtime = user_data[user]["total_playtime"] + user_data[friend]["total_playtime"]
			similarity = float(common_playtime) / total_playtime if total_playtime > 0 else 0

			# Add an edge between the user and their friend with
			# a different color to indicate whether they have
			# very similar interests, similar interests, 
			# or not similar interests
			if similarity > .25:
				graph.add_edge(user, friend, color='r')
			elif similarity > .125:
				graph.add_edge(user, friend, color='b')
			else:
				cross_links += 1
				graph.add_edge(user, friend, color='y')
			total_links += 1

# Calculate and print homophily value
print "Homophily index (max of 1) of this graph is: "+(str(1 - float(cross_links) / total_links) if total_links > 0 else "0")

# Display the graph
pos = nx.shell_layout(graph)
edges = graph.edges()
edge_colors = [graph[u][v]['color'] for u, v in edges]
node_colors = ['black' for node in graph.nodes()]
node_sizes = [10 for node in graph.nodes()]
nx.draw(graph, pos, edges=edges, edge_color=edge_colors, node_color=node_colors, node_size=node_sizes)
plt.show()
