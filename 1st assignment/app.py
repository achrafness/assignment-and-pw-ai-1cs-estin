from flask import Flask, render_template, request, jsonify
import heapq
import json

app = Flask(__name__)

# Define the maze as a graph (adjacency list)
maze_graph = {
    'A': {'1': 1},
    '1': {'A': 1, '2': 1},
    '2': {'1': 1, '3': 1, '4': 1},
    '3': {'2': 1, '5': 1},
    '4': {'2': 1, '10': 1},
    '5': {'3':1,'6': 1, '7': 1},
    '6': {'5': 1,'8': 1},
    '7': {'5': 1, '9': 1},
    '8': {'6': 1},
    '9': {'7': 1},
    '10': {'4': 1, '11': 1, '12': 1},
    '11': {'10': 1},
    '12': {'10': 1, '13': 1},
    '13': {'12': 1, '14': 1},
    '14': {'13': 1, '17': 1 ,'15': 1},
    '15': {'14':1,'16': 1},
    '16': {'15': 1},
    '17': {'14': 1, '18': 1, '20': 1},
    '18': {'17': 1, '19': 1},
    '19': {'18': 1},
    '20': {'17': 1, '21': 1},
    '21': {'20': 1, 'B': 1},
    'B': {'21': 1}
}

# Heuristic values for A* algorithm
heuristic = {
    'A': 8, '1': 6, '2': 6, '3': 6, '4': 7, '5': 4, 
    '6': 12, '7': 7, '8': 15, '9': 18, '10': 6, '11': 8, 
    '12': 6, '13': 5, '14': 4, '15': 8, '16': 6, '17': 3, 
    '18': 5, '19': 5, '20': 2, '21': 1, 'B': 0
}

# Define the maze for visualization
# 99 defines a wall
# 0 defines a path or empty space
maze_grid = [
    [8,99,9,99,11,99,99,99,18,19,99,'B'],
    [0,99,0,99,10,12,13,99,0,99,99,0],
    [6,5,7,99,0,99,14,0,17,99,99,0],
    [99,0,99,99,0,99,0,99,0,99,99,0],
    [99,3,0,2,4,99,0,99,20,0,0,21],
    [99,99,99,0,99,99,0,99,99,99,99,99],
    ['A',0,0,1,99,99,15,0,0,0,0,16],
]

# Positions for visualization
node_positions = {
    'A': {'x': 275, 'y': 420},
    '1': {'x': 370, 'y': 420},
    '2': {'x': 370, 'y': 315},
    '3': {'x': 315, 'y': 315},
    '4': {'x': 430, 'y': 315},
    '5': {'x': 315, 'y': 245},
    '6': {'x': 275, 'y': 245},
    '7': {'x': 370, 'y': 245},
    '8': {'x': 275, 'y': 175},
    '9': {'x': 370, 'y': 175},
    '10': {'x': 420, 'y': 210},
    '11': {'x': 420, 'y': 175},
    '12': {'x': 475, 'y': 245},
    '13': {'x': 530, 'y': 210},
    '14': {'x': 570, 'y': 245},
    '15': {'x': 540, 'y': 420},
    '16': {'x': 710, 'y': 420},
    '17': {'x': 640, 'y': 245},
    '18': {'x': 640, 'y': 175},
    '19': {'x': 685, 'y': 175},
    '20': {'x': 685, 'y': 315},
    '21': {'x': 755, 'y': 315},
    'B': {'x': 755, 'y': 175}
}

def bfs(start, goal):
    """Breadth-First Search algorithm"""
    queue = [(start, [start])]
    visited = set([start])
    all_explored = [start]
    
    while queue:
        vertex, path = queue.pop(0)
        if vertex == goal:
            return {'path': path, 'explored': all_explored}
        
        for neighbor in maze_graph.get(vertex, {}):
            if neighbor not in visited:
                visited.add(neighbor)
                all_explored.append(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return {'path': [], 'explored': all_explored}

def dfs(start, goal):
    """Depth-First Search algorithm"""
    stack = [(start, [start])]
    visited = set([start])
    all_explored = [start]
    
    while stack:
        vertex, path = stack.pop()
        if vertex == goal:
            return {'path': path, 'explored': all_explored}
        
        for neighbor in reversed(list(maze_graph.get(vertex, {}))):
            if neighbor not in visited:
                visited.add(neighbor)
                all_explored.append(neighbor)
                stack.append((neighbor, path + [neighbor]))
    
    return {'path': [], 'explored': all_explored}

def a_star(start, goal):
    """A* Search algorithm"""
    open_set = [(heuristic[start], 0, start, [start])]  # (f, g, node, path)
    closed_set = set()
    all_explored = [start]
    
    while open_set:
        f, g, node, path = heapq.heappop(open_set)
        
        if node == goal:
            return {'path': path, 'explored': all_explored}
        
        if node in closed_set:
            continue
            
        closed_set.add(node)
        
        for neighbor in maze_graph.get(node, {}):
            if neighbor in closed_set:
                continue
                
            if neighbor not in all_explored:
                all_explored.append(neighbor)
                
            new_g = g + maze_graph[node][neighbor]
            new_f = new_g + heuristic[neighbor]
            
            heapq.heappush(open_set, (new_f, new_g, neighbor, path + [neighbor]))
    
    return {'path': [], 'explored': all_explored}

@app.route('/')
def index():
    return render_template('index.html', 
                         maze_structure=json.dumps(maze_graph),
                         node_positions=json.dumps(node_positions),
                         maze_grid=json.dumps(maze_grid),
                         heuristic=json.dumps(heuristic))


@app.route('/solve', methods=['POST'])
def solve():
    algorithm = request.json.get('algorithm', 'bfs')
    start = request.json.get('start', 'A')
    goal = request.json.get('goal', 'B')
    
    if algorithm == 'bfs':
        result = bfs(start, goal)
    elif algorithm == 'dfs':
        result = dfs(start, goal)
    elif algorithm == 'astar':
        result = a_star(start, goal)
    else:
        return jsonify({'error': 'Invalid algorithm'})
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)