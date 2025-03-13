<script>
// Initialize variables
let mazeGraph = {{ maze_structure|safe }};
let nodePositions = {{ node_positions|safe }};

// Maze grid representation for visualization
const mazeGrid = {{ maze_grid|safe }};

// Node mapping to coordinates for visualization
const nodeCellMap = {};
const cellNodeMap = {};

// Global variables for animation
let animationInterval = null;
let currentAnimationStep = 0;
let exploredNodes = [];
let pathNodes = [];
let algorithmSteps = [];
let dataStructureSteps = [];
let robotElement = null;

// Create the maze on page load
document.addEventListener('DOMContentLoaded', function() {
    createMaze();
});

function createMaze() {
    const mazeContainer = document.getElementById('maze-container');
    mazeContainer.innerHTML = '';
    
    // Create robot element
    robotElement = document.createElement('div');
    robotElement.id = 'robot';
    robotElement.className = 'robot';
    robotElement.innerHTML = '<i class="fas fa-robot"></i>';
    mazeContainer.appendChild(robotElement);
    
    for (let row = 0; row < mazeGrid.length; row++) {
        for (let col = 0; col < mazeGrid[row].length; col++) {
            const cell = document.createElement('div');
            const value = mazeGrid[row][col];
            
            if (value === 99) {
                cell.className = 'cell wall';
            } else if (value === 0) {
                cell.className = 'cell path';
            } else {
                cell.className = 'cell node';
                if (value === 'A') {
                    cell.classList.add('start');
                } else if (value === 'B') {
                    cell.classList.add('goal');
                }
                
                // Add node label
                const label = document.createElement('div');
                label.className = 'node-label';
                label.textContent = value;
                cell.appendChild(label);
                
                // Map node to cell coordinates
                nodeCellMap[value] = {row, col};
                cellNodeMap[`${row},${col}`] = value;
            }
            
            mazeContainer.appendChild(cell);
        }
    }
    
    // Position the robot at start
    positionRobotAtNode('A');
}

function getCellCenter(row, col) {
    const cellSize = 50; // Must match CSS
    const gridGap = 2; // Must match CSS
    
    // Calculate the center of the cell (not the top-left corner)
    const x = col * (cellSize + gridGap) + cellSize / 2;
    const y = row * (cellSize + gridGap) + cellSize / 2;
    
    return {x, y};
}

function positionRobotAtNode(nodeId) {
    if (!nodeCellMap[nodeId] || !robotElement) return;
    
    const {row, col} = nodeCellMap[nodeId];
    const {x, y} = getCellCenter(row, col);
    
    // Position at the center of the cell
    robotElement.style.left = `${x}px`;
    robotElement.style.top = `${y}px`;
}

function openTab(tabId) {
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    
    const tabs = document.getElementsByClassName('tab');
    for (let i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('active');
    }
    
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}

async function solveMaze() {
    resetMaze();
    
    const algorithm = document.getElementById('algorithm').value;
    const solveButton = document.getElementById('solve-btn');
    solveButton.disabled = true;
    
    try {
        const response = await fetch('/solve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                algorithm: algorithm,
                start: 'A',
                goal: 'B'
            }),
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const result = await response.json();
        startAnimation(result.explored, result.path, algorithm);
    } catch (error) {
        console.error('Error:', error);
        alert('Error solving maze: ' + error.message);
    } finally {
        solveButton.disabled = false;
    }
}

function resetMaze() {
    if (animationInterval) {
        clearInterval(animationInterval);
        animationInterval = null;
    }
    
    currentAnimationStep = 0;
    exploredNodes = [];
    pathNodes = [];
    algorithmSteps = [];
    dataStructureSteps = [];
    
    // Reset cell styles
    const cells = document.querySelectorAll('.cell');
    cells.forEach(cell => {
        cell.classList.remove('visited', 'in-path');
    });
    
    // Reset robot position
    positionRobotAtNode('A');
    
    // Clear steps
    document.getElementById('steps-container').innerHTML = '';
    document.getElementById('data-structure-container').innerHTML = '';
}

function startAnimation(explored, path, algorithm) {
    exploredNodes = explored;
    pathNodes = path;
    
    // Generate algorithm steps
    generateAlgorithmSteps(algorithm, explored, path);
    
    const speed = document.getElementById('speed').value;
    const animationDelay = 1000 - speed; // Invert so higher value = faster
    
    currentAnimationStep = 0;
    
    animationInterval = setInterval(() => {
        if (currentAnimationStep < exploredNodes.length) {
            // Exploration phase
            const nodeId = exploredNodes[currentAnimationStep];
            highlightNode(nodeId, 'visited');
            updateAlgorithmStep(currentAnimationStep);
            currentAnimationStep++;
        } else if (currentAnimationStep < exploredNodes.length + pathNodes.length) {
            // Path tracing phase
            const pathIndex = currentAnimationStep - exploredNodes.length;
            const nodeId = pathNodes[pathIndex];
            highlightNode(nodeId, 'in-path');
            positionRobotAtNode(nodeId);
            updateAlgorithmStep(currentAnimationStep);
            currentAnimationStep++;
        } else {
            // Animation complete
            clearInterval(animationInterval);
            animationInterval = null;
        }
    }, animationDelay);
}

function highlightNode(nodeId, className) {
    if (!nodeCellMap[nodeId]) return;
    
    const {row, col} = nodeCellMap[nodeId];
    const cells = document.querySelectorAll('.cell');
    const index = row * mazeGrid[0].length + col;
    
    if (cells[index]) {
        cells[index].classList.add(className);
    }
}

function generateAlgorithmSteps(algorithm, explored, path) {
    algorithmSteps = [];
    dataStructureSteps = [];
    
    const dsTitle = document.getElementById('ds-title');
    
    if (algorithm === 'bfs') {
        dsTitle.textContent = 'Queue (FIFO)';
        
        // Initialize queue with start node
        let queue = ['A'];
        dataStructureSteps.push([...queue]);
        algorithmSteps.push("Step 0: Initialize queue with start node A");
        
        let visited = new Set(['A']);
        let stepCount = 1;
        
        for (let i = 0; i < explored.length; i++) {
            const node = explored[i];
            
            if (i > 0) { // Skip first node as it's already processed in initialization
                algorithmSteps.push(`Step ${stepCount}: Dequeue node ${node}`);
                // Remove first element from queue (FIFO)
                queue.shift();
                dataStructureSteps.push([...queue]);
                stepCount++;
            }
            
            // Get actual neighbors from the maze graph
            const neighbors = Object.keys(mazeGraph[node] || {})
                .filter(neighbor => !visited.has(neighbor));
            
            if (neighbors.length > 0) {
                algorithmSteps.push(`Step ${stepCount}: Add neighbors of ${node} to queue: ${neighbors.join(', ')}`);
                for (const neighbor of neighbors) {
                    visited.add(neighbor);
                    queue.push(neighbor);
                }
                dataStructureSteps.push([...queue]);
                stepCount++;
            }
            
            // Check if we've reached the goal
            if (node === 'B') {
                algorithmSteps.push(`Step ${stepCount}: Goal reached at node B!`);
                break;
            }
        }
    } else if (algorithm === 'dfs') {
        dsTitle.textContent = 'Stack (LIFO)';
        
        // Initialize stack with start node
        let stack = ['A'];
        dataStructureSteps.push([...stack]);
        algorithmSteps.push("Step 0: Initialize stack with start node A");
        
        let visited = new Set(['A']);
        let stepCount = 1;
        
        for (let i = 0; i < explored.length; i++) {
            const node = explored[i];
            
            if (i > 0) { // Skip first node as it's already processed in initialization
                algorithmSteps.push(`Step ${stepCount}: Pop node ${node} from stack`);
                // Remove last element from stack (LIFO)
                stack.pop();
                dataStructureSteps.push([...stack]);
                stepCount++;
            }
            
            // Get actual neighbors from the maze graph
            const neighbors = Object.keys(mazeGraph[node] || {})
                .filter(neighbor => !visited.has(neighbor))
                .reverse(); // Reverse to ensure correct DFS order
            
            if (neighbors.length > 0) {
                algorithmSteps.push(`Step ${stepCount}: Add neighbors of ${node} to stack: ${neighbors.join(', ')}`);
                for (const neighbor of neighbors) {
                    visited.add(neighbor);
                    stack.push(neighbor);
                }
                dataStructureSteps.push([...stack]);
                stepCount++;
            }
            
            // Check if we've reached the goal
            if (node === 'B') {
                algorithmSteps.push(`Step ${stepCount}: Goal reached at node B!`);
                break;
            }
        }
    } else if (algorithm === 'astar') {
        dsTitle.textContent = 'Priority Queue (sorted by f = g + h)';
        
        // For A*, we simulate the priority queue with format: [node, g, h, f]
        // Initialize priority queue with start node
        let priorityQueue = [['A', 0, heuristic['A'], heuristic['A']]];
        dataStructureSteps.push(formatPriorityQueue(priorityQueue));
        algorithmSteps.push(`Step 0: Initialize priority queue with A (g=0, h=${heuristic['A']}, f=${heuristic['A']})`);
        
        let visited = new Set();
        let gScores = { 'A': 0 };
        let stepCount = 1;
        
        for (let i = 0; i < explored.length; i++) {
            const node = explored[i];
            const currentG = gScores[node] || 0;
            
            // Add node to visited after popping from priority queue
            visited.add(node);
            
            if (i > 0) { // Skip first node as it's already processed in initialization
                algorithmSteps.push(`Step ${stepCount}: Remove node ${node} with lowest f-value from priority queue`);
                // Remove the first element (already sorted by f-value)
                priorityQueue.shift();
                dataStructureSteps.push(formatPriorityQueue(priorityQueue));
                stepCount++;
            }
            
            // Check if we've reached the goal
            if (node === 'B') {
                algorithmSteps.push(`Step ${stepCount}: Goal reached at node B!`);
                break;
            }
            
            // Get neighbors
            const neighbors = Object.keys(mazeGraph[node] || {});
            const unvisitedNeighbors = neighbors.filter(n => !visited.has(n));
            
            if (unvisitedNeighbors.length > 0) {
                algorithmSteps.push(`Step ${stepCount}: Evaluate neighbors of ${node}: ${unvisitedNeighbors.join(', ')}`);
                
                for (const neighbor of unvisitedNeighbors) {
                    const edgeCost = mazeGraph[node][neighbor] || 1;
                    const newG = currentG + edgeCost;
                    const h = heuristic[neighbor] || 0;
                    const f = newG + h;
                    
                    // Check if this is a better path
                    if (!gScores.hasOwnProperty(neighbor) || newG < gScores[neighbor]) {
                        gScores[neighbor] = newG;
                        algorithmSteps.push(`    Calculate for ${neighbor}: g=${newG}, h=${h}, f=${f}`);
                        
                        // Add to priority queue and sort by f-value
                        priorityQueue.push([neighbor, newG, h, f]);
                        priorityQueue.sort((a, b) => a[3] - b[3]); // Sort by f-value
                    }
                }
                
                dataStructureSteps.push(formatPriorityQueue(priorityQueue));
                stepCount++;
            }
        }
    }
    
    // Add final path information
    algorithmSteps.push(`\nFinal path found: ${path.join(' → ')}`);
    algorithmSteps.push(`Path length: ${path.length} nodes`);
    algorithmSteps.push(`Total nodes explored: ${explored.length} nodes`);
}

// Helper function to format priority queue for display
function formatPriorityQueue(queue) {
    if (queue.length === 0) return [];
    
    return queue.map(item => {
        const [node, g, h, f] = item;
        return `${node}(f=${f})`;
    });
}

function updateAlgorithmStep(step) {
    const stepsContainer = document.getElementById('steps-container');
    const dataStructureContainer = document.getElementById('data-structure-container');
    
    // Update algorithm steps
    if (step < algorithmSteps.length) {
        stepsContainer.innerHTML = algorithmSteps.slice(0, step + 1).join('\n');
        stepsContainer.scrollTop = stepsContainer.scrollHeight;
    }
    
    // Update data structure visualization
    if (step < dataStructureSteps.length) {
        dataStructureContainer.innerHTML = '';
        const items = dataStructureSteps[step];
        
        if (items && items.length > 0) {
            items.forEach((item, index) => {
                const itemEl = document.createElement('div');
                itemEl.className = 'data-item';
                if (index === 0 && items.length > 1) {
                    itemEl.classList.add('current-item'); // Highlight the active item
                }
                itemEl.textContent = item;
                dataStructureContainer.appendChild(itemEl);
            });
        } else {
            dataStructureContainer.textContent = '(empty)';
        }
    }
}

// Initialize maze
createMaze();
</script>